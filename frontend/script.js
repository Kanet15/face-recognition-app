// ตรวจสอบว่ามี axios หรือไม่
if (typeof axios === 'undefined') {
    console.error('axios is required. Please include axios library.');
}

document.getElementById('uploadForm').addEventListener('submit', async function(e) {
    e.preventDefault();
    
    // ดึงข้อมูลจากฟอร์ม
    const name = document.getElementById('name').value.trim();
    const id = document.getElementById('id').value.trim();
    const fileInput = document.getElementById('image');
    const file = fileInput.files[0];
    
    // Validation
    if (!validateForm(name, id, file)) {
        return;
    }
    
    // สร้าง FormData
    const formData = new FormData();
    formData.append('name', name);
    formData.append('id', id);
    formData.append('image', file);
    
    // แสดง loading state
    const submitBtn = e.target.querySelector('button[type="submit"]');
    const originalText = submitBtn.textContent;
    setLoading(submitBtn, true);
    
    try {
        // ส่งข้อมูลด้วย axios
        const response = await axios.post('http://localhost:8000/upload', formData, {
            headers: {
                'Content-Type': 'multipart/form-data'
            },
            // Progress tracking
            onUploadProgress: function(progressEvent) {
                const percentCompleted = Math.round((progressEvent.loaded * 100) / progressEvent.total);
                updateProgressBar(percentCompleted);
            },
            // Timeout 30 seconds
            timeout: 30000
        });
        
        // Success handling
        handleSuccess(response.data);
        
    } catch (error) {
        // Error handling
        handleError(error);
        
    } finally {
        // Reset loading state
        setLoading(submitBtn, false, originalText);
        hideProgressBar();
    }
});

// ฟังก์ชันตรวจสอบข้อมูล
function validateForm(name, id, file) {
    const errors = [];
    
    if (!name) {
        errors.push('กรุณากรอกชื่อ');
    }
    
    if (!id) {
        errors.push('กรุณากรอก ID');
    }
    
    if (!file) {
        errors.push('กรุณาเลือกไฟล์รูปภาพ');
    } else {
        // ตรวจสอบประเภทไฟล์
        const allowedTypes = ['image/jpeg', 'image/jpg', 'image/png', 'image/gif'];
        if (!allowedTypes.includes(file.type)) {
            errors.push('กรุณาเลือกไฟล์รูปภาพ (JPEG, PNG, GIF เท่านั้น)');
        }
        
        // ตรวจสอบขนาดไฟล์ (5MB)
        const maxSize = 5 * 1024 * 1024; // 5MB
        if (file.size > maxSize) {
            errors.push('ขนาดไฟล์ต้องไม่เกิน 5MB');
        }
    }
    
    if (errors.length > 0) {
        showAlert(errors.join('\n'), 'error');
        return false;
    }
    
    return true;
}

// ฟังก์ชันจัดการ loading state
function setLoading(button, isLoading, originalText = 'Submit') {
    if (isLoading) {
        button.disabled = true;
        button.innerHTML = '<span class="spinner"></span> กำลังอัปโหลด...';
    } else {
        button.disabled = false;
        button.textContent = originalText;
    }
}

// ฟังก์ชันอัปเดต progress bar
function updateProgressBar(percent) {
    let progressContainer = document.getElementById('progressContainer');
    
    if (!progressContainer) {
        // สร้าง progress bar ถ้ายังไม่มี
        progressContainer = document.createElement('div');
        progressContainer.id = 'progressContainer';
        progressContainer.innerHTML = `
            <div class="progress-bar">
                <div class="progress-fill" id="progressFill"></div>
                <span class="progress-text" id="progressText">0%</span>
            </div>
        `;
        document.getElementById('uploadForm').appendChild(progressContainer);
    }
    
    const progressFill = document.getElementById('progressFill');
    const progressText = document.getElementById('progressText');
    
    progressFill.style.width = percent + '%';
    progressText.textContent = percent + '%';
    
    progressContainer.style.display = 'block';
}

// ฟังก์ชันซ่อน progress bar
function hideProgressBar() {
    const progressContainer = document.getElementById('progressContainer');
    if (progressContainer) {
        setTimeout(() => {
            progressContainer.style.display = 'none';
        }, 1000);
    }
}

// ฟังก์ชันจัดการเมื่อสำเร็จ
function handleSuccess(data) {
    showAlert(data.message || 'อัปโหลดสำเร็จ!', 'success');
    
    // Reset form
    document.getElementById('uploadForm').reset();
    
    // อัปเดต UI หรือรีโหลดข้อมูลใหม่
    // แทนที่จะ reload ทั้งหน้า ให้อัปเดตเฉพาะส่วนที่จำเป็น
    refreshDataList();
}

// ฟังก์ชันจัดการ error
function handleError(error) {
    console.error('Upload error:', error);
    
    let errorMessage = 'เกิดข้อผิดพลาดในการอัปโหลด';
    
    if (error.response) {
        // Server responded with error status
        const data = error.response.data;
        errorMessage = data.detail || data.message || `Error: ${error.response.status}`;
    } else if (error.request) {
        // Network error
        errorMessage = 'ไม่สามารถเชื่อมต่อกับเซิร์ฟเวอร์ได้';
    } else {
        // Other errors
        errorMessage = error.message || errorMessage;
    }
    
    showAlert(errorMessage, 'error');
}

// ฟังก์ชันแสดง alert ที่สวยกว่า
function showAlert(message, type = 'info') {
    // ใช้ library เช่น SweetAlert2 หรือสร้าง custom alert
    if (typeof Swal !== 'undefined') {
        Swal.fire({
            title: type === 'success' ? 'สำเร็จ!' : 'แจ้งเตือน',
            text: message,
            icon: type,
            confirmButtonText: 'ตกลง'
        });
    } else {
        // Fallback to regular alert
        alert(message);
    }
}

// ฟังก์ชันรีเฟรชรายการข้อมูล (แทนการ reload ทั้งหน้า)
function refreshDataList() {
    // เรียก API เพื่อดึงข้อมูลใหม่และอัปเดต UI
    // ตัวอย่าง:
    // fetchDataList().then(updateUI);
}

// เพิ่ม CSS สำหรับ progress bar และ spinner
const style = document.createElement('style');
style.textContent = `
    .progress-bar {
        width: 100%;
        height: 20px;
        background-color: #f0f0f0;
        border-radius: 10px;
        overflow: hidden;
        margin: 10px 0;
        position: relative;
    }
    
    .progress-fill {
        height: 100%;
        background: linear-gradient(90deg, #4CAF50, #45a049);
        transition: width 0.3s ease;
    }
    
    .progress-text {
        position: absolute;
        top: 50%;
        left: 50%;
        transform: translate(-50%, -50%);
        font-size: 12px;
        font-weight: bold;
        color: #333;
    }
    
    .spinner {
        display: inline-block;
        width: 16px;
        height: 16px;
        border: 2px solid #f3f3f3;
        border-top: 2px solid #3498db;
        border-radius: 50%;
        animation: spin 1s linear infinite;
    }
    
    @keyframes spin {
        0% { transform: rotate(0deg); }
        100% { transform: rotate(360deg); }
    }
    
    #progressContainer {
        display: none;
    }
`;
document.head.appendChild(style);