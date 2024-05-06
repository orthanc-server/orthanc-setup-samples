This is a sample setup to convert a mp4 video into a multi-frame DICOM image

```
docker compose up --build

curl http://localhost:8042/video-to-cine --data-binary @sample-masked-video.mp4

```

Then, open [http://localhost:8042/ui/app/](http://localhost:8042/ui/app/)