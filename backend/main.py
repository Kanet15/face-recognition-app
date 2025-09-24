from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Body
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import os
import shutil
import logging
from typing import List, Dict, Any
import base64
from io import BytesIO
from PIL import Image
import numpy as np

# Import utilities robustly
try:
    # Try importing from the same directory (backend/)
    from utils import (
        get_face_encoding, 
        save_face_encoding_data, 
        recognize_face, 
        get_all_known_faces,
        recognize_faces_in_image
    )
except ImportError:
    try:
        # Try importing with explicit backend prefix
        from backend.utils import (
            get_face_encoding, 
            save_face_encoding_data, 
            recognize_face, 
            get_all_known_faces,
            recognize_faces_in_image
        )
    except ImportError:
        # Last resort: load utils.py by file path
        import importlib.util
        import sys
        
        # Since this file is in backend/, utils.py is in the same directory
        module_dir = os.path.dirname(__file__)
        utils_path = os.path.join(module_dir, 'utils.py')
        
        if os.path.exists(utils_path):
            spec = importlib.util.spec_from_file_location('utils', utils_path)
            utils_module = importlib.util.module_from_spec(spec)
            sys.modules['utils'] = utils_module
            spec.loader.exec_module(utils_module)
            
            # Import functions from the loaded module
            get_face_encoding = utils_module.get_face_encoding
            save_face_encoding_data = utils_module.save_face_encoding_data
            recognize_face = utils_module.recognize_face
            get_all_known_faces = utils_module.get_all_known_faces
            recognize_faces_in_image = utils_module.recognize_faces_in_image
        else:
            raise ImportError(f"Cannot find utils.py at {utils_path}")

app = FastAPI(title="Face Recognition System API")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

UPLOAD_FOLDER = "/backend/uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@app.get("/")
async def root():
    return {"message": "Face Recognition System API is running!"}

@app.post("/upload")
async def upload_face(
    name: str = Form(...),
    user_id: str = Form(...),
    image: UploadFile = File(...)
):
    if not name or not user_id:
        raise HTTPException(status_code=400, detail="กรุณาระบุชื่อและรหัส")

    if not image.filename:
        raise HTTPException(status_code=400, detail="กรุณาเลือกไฟล์")

    file_extension = os.path.splitext(image.filename)[1].lower()
    if file_extension not in ['.jpg', '.jpeg', '.png']:
        raise HTTPException(status_code=400, detail="รองรับไฟล์ .jpg, .jpeg, .png เท่านั้น")

    filename = f"{name}_{user_id}{file_extension}"
    filepath = os.path.join(UPLOAD_FOLDER, filename)

    try:
        with open(filepath, "wb") as buffer:
            shutil.copyfileobj(image.file, buffer)
        logger.info(f"บันทึกภาพ '{filename}' แล้ว")

        encoding = get_face_encoding(filepath)
        logger.info(f"สร้าง Face Encoding สำหรับ {name} ({user_id}) แล้ว")

        save_face_encoding_data(name, user_id, encoding)
        logger.info(f"บันทึกข้อมูลใบหน้าของ {name} ({user_id}) แล้ว")

        return JSONResponse(
            status_code=200,
            content={"message": "อัปโหลดและบันทึกข้อมูลใบหน้าเรียบร้อย!", "name": name, "id": user_id}
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"เกิดข้อผิดพลาด: {e}")
        raise HTTPException(status_code=500, detail=f"Server Error: {e}")
    finally:
        if os.path.exists(filepath):
            os.remove(filepath)
            logger.info(f"ลบไฟล์ชั่วคราว '{filepath}' แล้ว")

@app.post("/recognize")
async def recognize_face_endpoint(
    image: UploadFile = File(...)
):
    if not image.filename:
        raise HTTPException(status_code=400, detail="กรุณาเลือกไฟล์")

    file_extension = os.path.splitext(image.filename)[1].lower()
    if file_extension not in ['.jpg', '.jpeg', '.png']:
        raise HTTPException(status_code=400, detail="รองรับไฟล์ .jpg, .jpeg, .png เท่านั้น")

    filename = f"temp_recognize_{image.filename}"
    filepath = os.path.join(UPLOAD_FOLDER, filename)

    try:
        with open(filepath, "wb") as buffer:
            shutil.copyfileobj(image.file, buffer)
        logger.info(f"บันทึกภาพชั่วคราวสำหรับการจำแนก '{filename}' แล้ว")

        encoding = get_face_encoding(filepath)
        name, user_id, confidence = recognize_face(encoding)

        if name and user_id:
            return JSONResponse(
                status_code=200,
                content={
                    "message": "จำแนกใบหน้าสำเร็จ!",
                    "name": name,
                    "id": user_id,
                    "confidence": round(confidence, 3)
                }
            )
        else:
            return JSONResponse(
                status_code=404,
                content={"message": "ไม่พบใบหน้าที่ตรงกันในระบบ"}
            )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"เกิดข้อผิดพลาดในการจำแนกใบหน้า: {e}")
        raise HTTPException(status_code=500, detail=f"Server Error: {e}")
    finally:
        if os.path.exists(filepath):
            os.remove(filepath)
            logger.info(f"ลบไฟล์ชั่วคราว '{filepath}' แล้ว")

@app.get("/known-faces")
async def get_known_faces():
    try:
        faces = get_all_known_faces()
        return JSONResponse(
            status_code=200,
            content={"faces": faces, "total": len(faces)}
        )
    except Exception as e:
        logger.error(f"เกิดข้อผิดพลาดในการดึงข้อมูลใบหน้า: {e}")
        raise HTTPException(status_code=500, detail=f"Server Error: {e}")

@app.post("/recognize_realtime")
async def recognize_realtime(data: dict = Body(...)):
    """
    รับรูปภาพจาก Webcam (Base64 JPEG) แล้วส่งคืนข้อมูลใบหน้าทุกใบหน้าที่ตรวจจับได้
    """
    if recognize_faces_in_image is None:
        raise HTTPException(status_code=500, detail="ระบบยังไม่พร้อมสำหรับ realtime recognition")

    image_data = data.get("image")
    if not image_data or not isinstance(image_data, str):
        raise HTTPException(status_code=400, detail="ไม่มีข้อมูลรูปภาพ (base64)")

    try:
        # Remove header ("data:image/jpeg;base64,")
        if "," in image_data:
            image_data = image_data.split(",")[1]
        image_bytes = base64.b64decode(image_data)
        img = Image.open(BytesIO(image_bytes)).convert("RGB")
        img_array = np.array(img)

        # ใช้ฟังก์ชันใน utils.py
        faces = recognize_faces_in_image(img_array)
        return JSONResponse(status_code=200, content={"faces": faces})
    except Exception as e:
        logger.error(f"เกิดข้อผิดพลาดในการ realtime recognize: {e}")
        raise HTTPException(status_code=500, detail=f"Server Error: {e}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)