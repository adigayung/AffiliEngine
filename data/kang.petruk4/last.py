import cv2

video_path = "a.mp4"
output_image = "last_frame.jpg"

cap = cv2.VideoCapture(video_path)

last_frame = None

while True:
    ret, frame = cap.read()
    if not ret:
        break
    last_frame = frame

cap.release()

if last_frame is not None:
    cv2.imwrite(output_image, last_frame)
    print("Frame terakhir berhasil disimpan")
else:
    print("Tidak ada frame ditemukan")