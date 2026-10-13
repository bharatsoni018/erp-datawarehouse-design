// ERP Data Warehouse and Decision Support System JS

document.addEventListener('DOMContentLoaded', () => {
    // Automatically uppercase enrollment inputs as user types
    const enrollmentInputs = document.querySelectorAll('input[name="enrollment_no"]');
    enrollmentInputs.forEach(input => {
        input.addEventListener('input', (e) => {
            e.target.value = e.target.value.toUpperCase();
        });
    });
});
