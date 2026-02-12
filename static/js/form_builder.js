let fields = [];

function addField(fieldData = null) {
    const container = document.getElementById("fieldsContainer");

    const field = fieldData || {
        label: "",
        type: "text",
        options: []
    };

    const index = fields.length;
    fields.push(field);

    const fieldDiv = document.createElement("div");
    fieldDiv.classList.add("border", "p-3", "mb-3");

    fieldDiv.innerHTML = `
        <input type="text" class="form-control mb-2"
               placeholder="Field Label"
               value="${field.label}"
               onchange="updateField(${index}, 'label', this.value)">

        <select class="form-control mb-2"
                onchange="updateField(${index}, 'type', this.value)">
            <option value="text" ${field.type==="text"?"selected":""}>Text</option>
            <option value="number" ${field.type==="number"?"selected":""}>Number</option>
            <option value="select" ${field.type==="select"?"selected":""}>Select</option>
            <option value="checkbox" ${field.type==="checkbox"?"selected":""}>Checkbox</option>
            <option value="date" ${field.type==="date"?"selected":""}>Date</option>
        </select>

        <textarea class="form-control"
                  placeholder="Options (comma separated)"
                  onchange="updateOptions(${index}, this.value)">
                  ${field.options ? field.options.join(",") : ""}
        </textarea>

        <button type="button" class="btn btn-danger mt-2"
                onclick="removeField(${index})">
                Remove
        </button>
    `;

    container.appendChild(fieldDiv);
}

function updateField(index, key, value) {
    fields[index][key] = value;
}

function updateOptions(index, value) {
    fields[index].options = value.split(",").map(o => o.trim());
}

function removeField(index) {
    fields.splice(index, 1);
    document.getElementById("fieldsContainer").innerHTML = "";
    fields.forEach(f => addField(f));
}

document.getElementById("formBuilderForm").addEventListener("submit", function() {
    document.getElementById("fields_json").value = JSON.stringify(fields);
});

if (typeof existingFields !== "undefined") {
    existingFields.forEach(f => addField(f));
}