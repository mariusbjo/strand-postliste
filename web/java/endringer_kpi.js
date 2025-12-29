// ===============================
//  endringer_kpi.js
//  KPI-beregninger og rendering
// ===============================

export function renderKPIs(changes, postliste) {

    const now = new Date();
    const days30 = new Date(now.getTime() - 30 * 24 * 60 * 60 * 1000);

    const recent = changes.filter(c => new Date(c.tidspunkt) >= days30);

    const newDocs = recent.filter(c => c.type === "NEW").length;
    const updatedDocs = recent.filter(c => c.type === "UPDATE").length;

    const changeRate = newDocs + updatedDocs > 0
        ? Math.round((updatedDocs / (newDocs + updatedDocs)) * 100)
        : 0;

    const newFiles = recent.filter(c =>
        c.endringer && c.endringer.filer_count
    ).length;

    const statusChanges = recent.filter(c =>
        c.endringer && c.endringer.status
    ).length;

    // Render
    document.getElementById("kpi-new-docs-value").textContent = newDocs;
    document.getElementById("kpi-updated-docs-value").textContent = updatedDocs;
    document.getElementById("kpi-change-rate-value").textContent = changeRate + "%";
    document.getElementById("kpi-new-files-value").textContent = newFiles;
    document.getElementById("kpi-status-changes-value").textContent = statusChanges;
}
