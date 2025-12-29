// ===============================
//  endringer_graphs.js
//  Grafer for dashboardet
// ===============================

export function renderGraphs(changes, postliste) {

    // 1. Endringer over tid
    const perDay = {};

    for (const c of changes) {
        const d = c.tidspunkt.slice(0, 10);
        perDay[d] = (perDay[d] || 0) + 1;
    }

    const labels = Object.keys(perDay).sort();
    const values = labels.map(d => perDay[d]);

    new Chart(
        document.getElementById("graph-changes-over-time"),
        {
            type: "line",
            data: {
                labels,
                datasets: [{
                    label: "Endringer per dag",
                    data: values,
                    borderColor: "#0077cc",
                    fill: false
                }]
            }
        }
    );

    // 2. Endringer per dokumenttype
    const perType = {};

    for (const c of changes) {
        const doc = postliste[c.dokumentID];
        if (!doc) continue;

        const type = doc.dokumenttype || "Ukjent";
        perType[type] = (perType[type] || 0) + 1;
    }

    new Chart(
        document.getElementById("graph-by-type"),
        {
            type: "bar",
            data: {
                labels: Object.keys(perType),
                datasets: [{
                    label: "Endringer per dokumenttype",
                    data: Object.values(perType),
                    backgroundColor: "#44aadd"
                }]
            }
        }
    );

    // 3. Hvilke felter endres mest?
    const fieldCounts = {};

    for (const c of changes) {
        if (!c.endringer) continue;
        for (const field of Object.keys(c.endringer)) {
            fieldCounts[field] = (fieldCounts[field] || 0) + 1;
        }
    }

    new Chart(
        document.getElementById("graph-field-changes"),
        {
            type: "bar",
            data: {
                labels: Object.keys(fieldCounts),
                datasets: [{
                    label: "Endringer per felt",
                    data: Object.values(fieldCounts),
                    backgroundColor: "#ffaa33"
                }]
            }
        }
    );
}
