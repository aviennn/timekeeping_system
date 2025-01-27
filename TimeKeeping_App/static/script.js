function updateClock() {
    const options = { 
        dateStyle: 'full',
        timeStyle: 'medium',
        timeZone: 'Asia/Manila'
    };
    document.getElementById('clock').textContent = 
        new Date().toLocaleString('en-US', options);
}

document.addEventListener('DOMContentLoaded', () => {
    setInterval(updateClock, 1000);
    updateClock();
});

function togglePassword() {
    const passwordField = document.getElementById('password');
    const eyeIcon = document.getElementById('eye-icon');
    if (passwordField.type === 'password') {
        passwordField.type = 'text';
        eyeIcon.classList.replace('fa-eye', 'fa-eye-slash'); 
    } else {
        passwordField.type = 'password';
        eyeIcon.classList.replace('fa-eye-slash', 'fa-eye'); 
    }
}

function sortTable(columnIndex, dataType) {
    const table = document.querySelector('table');
    const rows = Array.from(table.rows).slice(1);
    const header = table.rows[0].cells[columnIndex];
    const isAscending = header.classList.contains("ascending");

    Array.from(table.rows[0].cells).forEach(th => {
        th.classList.remove("ascending", "descending");
    });

    rows.sort((rowA, rowB) => {
        const cellA = rowA.cells[columnIndex].textContent.trim();
        const cellB = rowB.cells[columnIndex].textContent.trim();

        let valueA, valueB;

        if (dataType === "date") {
            valueA = new Date(cellA);
            valueB = new Date(cellB);
        } else if (dataType === "number") {
            valueA = parseFloat(cellA);
            valueB = parseFloat(cellB);
        } else {
            valueA = cellA.toLowerCase();
            valueB = cellB.toLowerCase();
        }

        if (isAscending) {
            return valueA > valueB ? -1 : 1;
        } else {
            return valueA < valueB ? -1 : 1;
        }
    });

    rows.forEach(row => table.appendChild(row));

    if (isAscending) {
        header.classList.add("descending");
    } else {
        header.classList.add("ascending");
    }
}

document.querySelectorAll('th').forEach((header, index) => {
    let dataType = "string";
    if (header.textContent.toLowerCase().includes("date")) {
        dataType = "date";
    } else if (header.textContent.toLowerCase().includes("hours")) {
        dataType = "number";
    }

    header.addEventListener('click', () => {
        sortTable(index, dataType);
    });
});
