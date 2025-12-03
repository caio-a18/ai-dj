import os
import uuid
from decimal import Decimal
import boto3
import requests
import io
import librosa
import numpy as np
import torch
import pandas as pd
from torch.utils.data import DataLoader
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
from spotipy.oauth2 import SpotifyOAuth
from dotenv import load_dotenv
# -------------------------------------------------------------------
# Spotify API setup
# Set up authentication with your Spotify Developer credentials
load_dotenv()
client_id = os.getenv("CLIENT_ID")
client_secret = os.getenv("CLIENT_SECRET")
sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
    scope="playlist-modify-public playlist-modify-private",
    client_id=client_id,
    client_secret=client_secret,
    redirect_uri="http://127.0.0.1:5173/callback"
))
# -------------------------------------------------------------------
# 0. AWS / DynamoDB setup
# -------------------------------------------------------------------
session = boto3.Session(profile_name='DevMusic4You-411189321562', region_name='us-east-2')
dynamodb = session.resource('dynamodb')
s3 = session.client("s3")
BUCKET_NAME = "aidj-data"

# Get or create aidj_playlists table
def get_or_create_playlists_table():
    existing_tables = dynamodb.meta.client.list_tables()["TableNames"]
    if "aidj_playlists" in existing_tables:
        print("Using existing table: aidj_playlists")
        return dynamodb.Table("aidj_playlists")

    print("Creating table: aidj_playlists")
    table = dynamodb.create_table(
        TableName='aidj_playlists',
        AttributeDefinitions=[
            {
                'AttributeName': 'playlist_id',
                'AttributeType': 'S',
            },
        ],
        KeySchema=[
            {
                'AttributeName': 'playlist_id',
                'KeyType': 'HASH',
            },
        ],
        BillingMode='PAY_PER_REQUEST',
    )
    table.wait_until_exists()
    print("Table created.")
    return table

playlist_table = get_or_create_playlists_table()

# Existing dataset table
datasets_table = dynamodb.Table('aidj_datasets')

# -------------------------------------------------------------------
# 1. Deezer helpers
# -------------------------------------------------------------------
def get_deezer_preview_url(track_name, artist_name=None):
    query = f"{track_name}"
    if artist_name:
        query += f" {artist_name}"
    url = f"https://api.deezer.com/search/track?q={query}"
    response = requests.get(url)
    if response.status_code != 200:
        print(f"API request failed with status {response.status_code} for track {track_name}")
        return None
    try:
        data = response.json()
    except ValueError:
        print(f"Invalid JSON response for track {track_name}")
        return None
    if 'data' in data and data['data']:
        return data['data'][0].get('preview')
    return None


def download_preview(preview_url, output_filename):
    response = requests.get(preview_url)
    with open(output_filename, 'wb') as f:
        f.write(response.content)
    print(f"Downloaded preview to {output_filename}")


def extract_mel_spectrogram_features(filename, n_mels=32, fmax=8000):
    y, sr = librosa.load(filename, sr=None)
    mel_spect = librosa.feature.melspectrogram(y=y, sr=sr, n_mels=n_mels, fmax=fmax)
    mel_spect_db = librosa.power_to_db(mel_spect, ref=np.max)
    return np.concatenate((mel_spect_db.mean(axis=1), mel_spect_db.std(axis=1)))


def process_user_input_song(track_title, artist_name=None):
    preview_url = get_deezer_preview_url(track_title, artist_name)
    if preview_url:
        tmp_filename = f'temp_{track_title[:10].replace(" ", "_")}.mp3'
        try:
            download_preview(preview_url, tmp_filename)
            features = extract_mel_spectrogram_features(tmp_filename)
            os.remove(tmp_filename)
            print(f"Extracted features for '{track_title}' by '{artist_name}':")
            print(features)
            return features
        except Exception as e:
            print(f"Error processing {track_title}: {e}")
            return None
    else:
        print(f"No preview URL for track: {track_title}")
        return None

# -------------------------------------------------------------------
# 2. DynamoDB upload for features (existing)
# -------------------------------------------------------------------
def upload_features_to_dynamodb(table, track_title, artist_name, features):
    item = {
        "id": str(uuid.uuid4()),   # UUID as primary key, type S in table
        "track_title": track_title,
        "artist_name": artist_name,
    }
    for i, val in enumerate(features):
        item[f"mel_feat_{i}"] = Decimal(str(val))  # DynamoDB Number

    table.put_item(Item=item)
    print("Song added to aidj_datasets")

# -------------------------------------------------------------------
# 3. Playlist table writer
# -------------------------------------------------------------------
def save_playlist_to_dynamodb(playlist_table,
                              track_title,
                              artist_name,
                              song_amount,
                              playlist_uris,
                              spotify_playlist_id=None):
    """
    playlist_uris: list of Spotify track URI strings
    """
    item = {
        "playlist_id": str(uuid.uuid4()),  # primary key
        "track_title": track_title,
        "artist_name": artist_name,
        "song_amount": int(song_amount),
        "playlist": playlist_uris,         # DynamoDB List of strings
    }
    if spotify_playlist_id is not None:
        item["spotify_playlist_id"] = spotify_playlist_id

    playlist_table.put_item(Item=item)
    print("Playlist saved to aidj_playlists")

# -------------------------------------------------------------------
# 4. Model / dataset (you already have this defined elsewhere)
# -------------------------------------------------------------------
# Assumes:
#   - MelFeatureDataset
#   - MelFeatureEmbedding model
#   - model has been trained and loaded, then model.eval()

class MelFeatureDataset(torch.utils.data.Dataset):
    def __init__(self, csv_file):
        df = pd.read_csv(csv_file)
        self.X = df[[col for col in df.columns if "mel_feat" in col]].values.astype("float32")
        self.y = df['genre_id'].values.astype("int64") if 'genre_id' in df.columns else None

    def __len__(self):
        return len(self.X)

    def __getitem__(self, idx):
        feat = torch.tensor(self.X[idx], dtype=torch.float32)
        if self.y is not None:
            return feat, torch.tensor(self.y[idx], dtype=torch.long)
        return feat


class MelFeatureEmbedding(torch.nn.Module):
    def __init__(self, input_dim=64, embedding_dim=64, num_classes=10):
        super().__init__()
        self.fc1 = torch.nn.Linear(input_dim, 128)
        self.fc2 = torch.nn.Linear(128, embedding_dim)
        self.classifier = torch.nn.Linear(embedding_dim, num_classes)
        self.dropout = torch.nn.Dropout(0.2)

    def forward(self, x):
        x = torch.nn.functional.relu(self.fc1(x))
        x = self.dropout(x)
        emb = self.fc2(x)
        logits = self.classifier(emb)
        return logits, emb

# Load trained model (if you have it saved)
MODEL_PATH = "mel_embedding_model.pth"
model = MelFeatureEmbedding(input_dim=64, embedding_dim=64, num_classes=10)
if os.path.exists(MODEL_PATH):
    model.load_state_dict(torch.load(MODEL_PATH, map_location="cpu"))
    print("Loaded model weights from", MODEL_PATH)
model.eval()

# -------------------------------------------------------------------
# 5. Main flow: user input, features, recommendations, playlist, DynamoDB
# -------------------------------------------------------------------
artist = input("Enter artist name: ")
song = input("Enter song name: ")
number_of_songs = int(input("Enter number of recommendations: "))
extra_recs = 10
total_recs = number_of_songs + extra_recs

# Extract features for user song
new_song_features = process_user_input_song(song, artist)

# Load all existing items from aidj_datasets
response = datasets_table.scan()
items = response['Items']
while 'LastEvaluatedKey' in response:
    response = datasets_table.scan(ExclusiveStartKey=response['LastEvaluatedKey'])
    items.extend(response['Items'])

df = pd.DataFrame(items)

feature_cols = [f"mel_feat_{i}" for i in range(64)]
titles = df['track_title'].tolist()
artists_names = df['artist_name'].tolist()
features = df[feature_cols].values.astype('float32')
features_tensor = torch.tensor(features)

# Also store the new song into aidj_datasets for future recommendations
if new_song_features is not None:
    upload_features_to_dynamodb(datasets_table, song, artist, new_song_features)

# Compute embeddings for all existing tracks
with torch.no_grad():
    _, all_embeddings = model(features_tensor)

# Recommendation: cosine similarity
if new_song_features is not None:
    query_features = torch.tensor(new_song_features, dtype=torch.float32).unsqueeze(0)
    with torch.no_grad():
        _, query_embedding = model(query_features)
    cos = torch.nn.CosineSimilarity(dim=1)
    similarities = cos(query_embedding, all_embeddings)
    sorted_indices = torch.argsort(similarities, descending=True).tolist()
    filtered_titles = []
    for idx in sorted_indices:
        if titles[idx].strip().lower() != song.strip().lower():
            filtered_titles.append((titles[idx], artists_names[idx]))
        if len(filtered_titles) == total_recs:
            break
    print("Top", total_recs, "predicted songs (excluding input):")
    for title, a in filtered_titles:
        print(f"Title: {title} | Artist: {a}")
else:
    print("Could not extract features for the input song.")
    filtered_titles = []

# -------------------------------------------------------------------
# 6. Spotify playlist creation + URIs
# -------------------------------------------------------------------
# Assumes you already have a Spotipy client "sp" authenticated
user_id = sp.current_user()['id']
playlist = sp.user_playlist_create(
    user=user_id,
    name=f"{artist}, {song}, playlist",
    public=True,
    description="Created with Spotipy"
)
print("Created playlist:", playlist['name'], "ID:", playlist['id'])

def get_track_uri(track_title, artist_name=None):
    query = f"track:{track_title}"
    if artist_name:
        query += f" artist:{artist_name}"
    results = sp.search(q=query, type='track', limit=1)
    if results['tracks']['items']:
        return results['tracks']['items'][0]['uri']
    return None

# Build list of URIs to add
input_uri = get_track_uri(song, artist)
if input_uri is not None:
    uris_to_add = [input_uri]
    added_titles = {(song, artist)}
    print(f"Input song found and will be added as the first track: {song} by {artist}")
else:
    uris_to_add = []
    added_titles = set()
    print(f"Input song not found on Spotify; will add only recommendations.")

i = 0
while len(uris_to_add) < number_of_songs and i < len(filtered_titles):
    title, a = filtered_titles[i]
    if (title, a) in added_titles:
        i += 1
        continue
    uri = get_track_uri(title, a)
    if uri is not None:
        uris_to_add.append(uri)
        added_titles.add((title, a))
    else:
        print(f"Could not find URI for {title} by {a}, skipping.")
    i += 1

if uris_to_add:
    sp.playlist_add_items(playlist_id=playlist['id'], items=uris_to_add)
    print(f"Added {len(uris_to_add)} songs to playlist.")
else:
    print("No valid URIs found to add to playlist.")

# -------------------------------------------------------------------
# 7. Save playlist record to aidj_playlists
# -------------------------------------------------------------------
save_playlist_to_dynamodb(
    playlist_table=playlist_table,
    track_title=song,
    artist_name=artist,
    song_amount=number_of_songs,
    playlist_uris=uris_to_add,
    spotify_playlist_id=playlist['id']
)
