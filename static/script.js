document.addEventListener("DOMContentLoaded", function () {
    const addRowBtn = document.getElementById("addRow");
    const tableBody = document.querySelector("#entryTable tbody");
    const rowCountInput = document.getElementById("row_count");

    addRowBtn.addEventListener("click", () => {
        let index = tableBody.rows.length + 1;
        const row = document.createElement("tr");
        const fields = ['sno', 'name', 'roll', 'asmt', 'quiz', 'total', 'mst1', 'mst2', 'best', 'external', 'gtotal'];
        fields.forEach(field => {
            const cell = document.createElement("td");
            cell.innerHTML = `<input name="${field}_${index}" class="form-control">`;
            row.appendChild(cell);
        });
        row.innerHTML += `<td><button type="button" class="btn btn-danger btn-sm remove-row">✖</button></td>`;
        tableBody.appendChild(row);
        rowCountInput.value = index;
    });

    tableBody.addEventListener("click", function (e) {
        if (e.target.classList.contains("remove-row")) {
            e.target.closest("tr").remove();
            rowCountInput.value = tableBody.rows.length;
        }
    });
});
