document.addEventListener('DOMContentLoaded', () => {
    const ctx = document.getElementById('emotionChart').getContext('2d');
    let emotionChart; // Biến để lưu trữ đối tượng biểu đồ

    const fetchAndDrawChart = async (days) => {
        const endDate = new Date();
        const startDate = new Date();
        startDate.setDate(endDate.getDate() - days);

        const apiUrl = `http://127.0.0.1:8000/dashboard-data?start_date=${startDate.toISOString().split('T')[0]}&end_date=${endDate.toISOString().split('T')[0]}`;
        
        try {
            const response = await fetch(apiUrl);
            const data = await response.json();

            const labels = data.map(item => item.date);
            const positiveData = data.map(item => item.positive_avg);
            const negativeData = data.map(item => item.negative_avg);
            const socialData = data.map(item => item.social_avg);
            const selfEsteemData = data.map(item => item.self_esteem_avg);

            if (emotionChart) {
                emotionChart.destroy(); // Hủy biểu đồ cũ trước khi vẽ mới
            }

            emotionChart = new Chart(ctx, {
                type: 'bar',
                data: {
                    labels: labels,
                    datasets: [
                        {
                            label: 'Cảm xúc Tích cực (TB)',
                            data: positiveData,
                            borderColor: 'rgba(75, 192, 192, 1)',
                            backgroundColor: 'rgba(75, 192, 192, 0.2)',
                            tension: 0.3, fill: true,
                        },
                        {
                            label: 'Cảm xúc Tiêu cực (TB)',
                            data: negativeData,
                            borderColor: 'rgba(255, 99, 132, 1)',
                            backgroundColor: 'rgba(255, 99, 132, 0.2)',
                            tension: 0.3, fill: true,
                        },
                        {
                            label: 'Quan hệ Xã hội (TB)',
                            data: socialData,
                            backgroundColor: 'rgba(54, 162, 235, 0.7)', // Màu xanh dương
                            borderColor: 'rgba(54, 162, 235, 1)',
                            borderWidth: 1
                        },
                         {
                            label: 'Cảm xúc về Bản thân (TB)',
                            data: selfEsteemData,
                            borderColor: 'rgba(255, 206, 86, 1)',
                            backgroundColor: 'rgba(255, 206, 86, 0.2)',
                            tension: 0.3, fill: true,
                        }
                    ]
                },
                options: {
                    responsive: true,
                    scales: {
                        y: { beginAtZero: false, min: 1, max: 5, title: { display: true, text: 'Mức độ (Trung bình từ 1-5)' } },
                        x: { title: { display: true, text: 'Ngày' } }
                    }
                }
            });
        } catch (error) {
            console.error("Lỗi khi lấy dữ liệu biểu đồ:", error);
        }
    };

    document.getElementById('btn-7-days').addEventListener('click', () => fetchAndDrawChart(7));
    document.getElementById('btn-30-days').addEventListener('click', () => fetchAndDrawChart(30));

    // Mặc định tải dữ liệu của 30 ngày qua khi vào trang
    fetchAndDrawChart(30);
});