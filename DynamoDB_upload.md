aws dynamodb batch-write-item --request-items file://d:/CodingProjects/Capstone/ai-dj/aws/import/datasets_batch.json --profile aijdj --region us-east-2

aws dynamodb batch-write-item --request-items file://d:/CodingProjects/Capstone/ai-dj/aws/import/playlists_batch.json --profile aijdj --region us-east-2

aws dynamodb scan --table-name aidj_datasets --select COUNT --profile aijdj --region us-east-2

aws dynamodb get-item --table-name aidj-playlists --key '{"playlist_id":{"S":"00000000-0000-4000-8000-000000000001"}}' --profile aijdj --region us-east-2

aws dynamodb get-item --table-name aidj-playlists --key "{\"playlist_id\":{\"S\":\"00000000-0000-4000-8000-000000000001\"}}" --profile aijdj --region us-east-2

aws dynamodb get-item --table-name aidj-playlists --key '{"playlist_id":{"S":"00000000-0000-4000-8000-000000000001"}}' --profile aijdj --region us-east-2