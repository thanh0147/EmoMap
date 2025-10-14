   document.addEventListener('DOMContentLoaded', () => {
    
    const form = document.getElementById('emotionForm');
    const steps = document.querySelectorAll('.survey-step');
    const progressBarFill = document.querySelector('.progress-bar-fill');
    // (Trong file script.js, ngay dưới dòng `const form = ...`)
    const loadingModal = document.getElementById('loading-modal');
    const feedbackModal = document.getElementById('feedback-modal');
    const feedbackText = document.getElementById('feedback-text');
    const closeFeedbackBtn = document.getElementById('close-feedback-btn');
    // == PHẦN MỚI 1: Lấy phần tử mascot và tạo mảng cảm xúc ==
    const penguinMascot = document.getElementById('penguin-mascot');
    const penguinEmotions = [
        '😺', // 0. Bắt đầu
        '😸', // 1. Trả lời câu hỏi tích cực
        '😿', // 2. Trả lời câu hỏi tiêu cực
        '😹', // 3. Trả lời câu hỏi xã hội
        '😻', // 4. Trả lời câu hỏi về bản thân
        '🤗'  // 5. Viết chia sẻ cuối
    ];
    let currentStep = 0;

    const showStep = (stepIndex) => {
        steps.forEach((step, index) => {
            step.classList.toggle('active-step', index === stepIndex);
        });
        updateProgressBar();
        
        // == PHẦN MỚI 2: Cập nhật cảm xúc của chim cánh cụt ==
        if (penguinEmotions[stepIndex]) {
            penguinMascot.textContent = penguinEmotions[stepIndex];
            penguinMascot.style.transform = 'scale(1)'; // Reset hiệu ứng
            // Ép trình duyệt render lại để chạy animation
            void penguinMascot.offsetWidth; 
            penguinMascot.style.transform = 'scale(1.2)'; // Tạo hiệu ứng nảy lên
        }
    };

    const updateProgressBar = () => {
        const progress = ((currentStep + 1) / steps.length) * 100;
        progressBarFill.style.width = `${progress}%`;
    };
    
    // == PHẦN MỚI 3: Logic kiểm tra thông tin (Validation) ==
    const validateCurrentStep = () => {
        // Chỉ kiểm tra cho bước đầu tiên (index = 0)
        if (currentStep === 0) {
            const classNameInput = document.getElementById('className');
            const genderSelected = document.querySelector('input[name="gender"]:checked');
            
            // Kiểm tra Lớp có được điền không
            if (classNameInput.value.trim() === '') {
                alert('Bạn ơi, hãy cho EmoMap biết bạn học lớp nào nhé!');
                classNameInput.focus(); // Focus vào ô bị trống
                return false; // Chặn không cho đi tiếp
            }
            
            // Kiểm tra Giới tính đã được chọn chưa
            if (!genderSelected) {
                alert('Bạn vui lòng chọn giới tính của mình nhé!');
                return false; // Chặn không cho đi tiếp
            }
        }
        
        // Với các bước khác, luôn cho qua
        return true;
    };

    document.querySelectorAll('.btn-next').forEach(button => {
        button.addEventListener('click', () => {
            // == PHẦN MỚI 4: Thêm bước kiểm tra trước khi chuyển step ==
            if (validateCurrentStep()) {
                if (currentStep < steps.length - 1) {
                    currentStep++;
                    showStep(currentStep);
                }
            }
        });
    });

    document.querySelectorAll('.btn-prev').forEach(button => {
        button.addEventListener('click', () => {
            if (currentStep > 0) {
                currentStep--;
                showStep(currentStep);
            }
        });
    });
    
    // (Các phần code khác về ẩn danh, thanh trượt... giữ nguyên)
    // ...
  
    // --- XỬ LÝ CHỨC NĂNG ẨN DANH ---
    const anonymousCheckbox = document.getElementById('anonymous');
    const fullNameInput = document.getElementById('fullName');
    anonymousCheckbox.addEventListener('change', () => {
        if (anonymousCheckbox.checked) {
            fullNameInput.disabled = true;
            fullNameInput.value = 'Ẩn danh';
            fullNameInput.style.backgroundColor = '#f0f0f0';
        } else {
            fullNameInput.disabled = false;
            fullNameInput.value = '';
            fullNameInput.style.backgroundColor = '#ffffff';
        }
    });

    // --- XỬ LÝ CÁC THANH TRƯỢT LIKERT VÀ ICON ---
    document.querySelectorAll('.likert-item').forEach(item => {
        const slider = item.querySelector('.likert-slider');
        const icons = item.querySelectorAll('.likert-icons span');

        const updateIcons = (currentValue) => {
            icons.forEach(icon => {
                const iconValue = icon.getAttribute('data-value');
                // Chỉ thêm class 'active' cho icon khớp với giá trị slider
                icon.classList.toggle('active', iconValue == currentValue);
            });
        };

        slider.addEventListener('input', (event) => {
            updateIcons(event.target.value);
        });

        // Cập nhật trạng thái ban đầu khi tải trang
        updateIcons(slider.value);
    });


    
// (Trong file script.js)

// --- XỬ LÝ KHI GỬI FORM (PHIÊN BẢN MỚI) ---
// (Trong file script.js, thay thế toàn bộ khối `form.addEventListener('submit', ...)` cũ)

form.addEventListener('submit', async (event) => {
    event.preventDefault();

    // 1. Hiển thị pop-up loading
    loadingModal.classList.remove('hidden');

    // Lấy dữ liệu từ form
    const formData = new FormData(form);
    const data = Object.fromEntries(formData.entries());
    // Chuyển đổi các giá trị số từ string sang number
    for (let i = 1; i <= 8; i++) {
        const key = `q${i}`;
        if (data[key]) data[key] = parseInt(data[key], 10);
    }


    try {
        // --- Gửi dữ liệu đến địa chỉ của Backend ---
        const response = await fetch('https://emomap-backend.onrender.com/submit-survey', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data), // Chuyển dữ liệu thành chuỗi JSON
        });

        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.detail || 'Lỗi từ server');
        }

        const result = await response.json();
        
        // 3. Ẩn loading và hiển thị pop-up phản hồi
        loadingModal.classList.add('hidden');
        feedbackText.textContent = result.feedback;
        feedbackModal.classList.remove('hidden');

    } catch (error) {
        console.error('Lỗi khi gửi dữ liệu:', error);
        alert(`Rất tiếc, đã có lỗi xảy ra: ${error.message}`);
    } finally {
        loadingModal.classList.add('hidden'); // Luôn ẩn loading sau khi xong
    }
});

// 4. Thêm sự kiện để đóng pop-up phản hồi
const closeAndReset = () => {
    feedbackModal.classList.add('hidden');
    // Đợi hiệu ứng đóng kết thúc rồi mới reset form
    setTimeout(() => {
        penguinMascot.textContent = '🎉';
        currentStep = 0;
        showStep(currentStep);
        form.reset();
        // Kích hoạt lại logic ẩn danh nếu cần
        anonymousCheckbox.dispatchEvent(new Event('change'));
        // Reset lại trạng thái ban đầu của các slider
        document.querySelectorAll('.likert-slider').forEach(slider => {
            slider.value = 3;
            slider.dispatchEvent(new Event('input'));
        });
    }, 300);
};

closeFeedbackBtn.addEventListener('click', closeAndReset);

// Cho phép đóng modal khi click ra ngoài vùng pop-up
feedbackModal.addEventListener('click', (event) => {
    if (event.target === feedbackModal) {
        closeAndReset();
    }
});

    // --- KHỞI TẠO ---
    showStep(currentStep);

});
