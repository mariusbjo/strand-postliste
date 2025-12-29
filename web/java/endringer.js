// ===============================
//  Endringsdashboard – hovedfil
// ===============================

// Importer moduler
import { loadChanges, loadPostliste } from "./endringer_data.js";
import { renderKPIs } from "./endringer_kpi.js";
import { renderGraphs } from "./endringer_graphs.js";
import { renderTables } from "./endringer_tables.js";


// -------------------------------
//  INITIALISERING
// -------------------------------

async function initDashboard() {
    console.log("📊 Initialiserer endringsdashboard...");

    // 1. Last data
    const changes = await loadChanges();
    const postliste = await loadPostliste();

    // 2. KPI-er
    renderKPIs(changes, postliste);

    // 3. Grafer
    renderGraphs(changes, postliste);

    // 4. Tabeller
    renderTables(changes, postliste);

    console.log("✅ Dashboard ferdig lastet");
}


// -------------------------------
//  START
// -------------------------------

document.addEventListener("DOMContentLoaded", initDashboard);

// ===============================
//  COLLAPSIBLES
// ===============================

function initCollapsibles() {
    const headers = document.querySelectorAll(".collapsible-header");

    headers.forEach(header => {
        header.addEventListener("click", () => {
            header.parentElement.classList.toggle("open");
        });
    });

    // Åpne/lukke alle knapper
    const openAllBtn = document.getElementById("open-all");
    const closeAllBtn = document.getElementById("close-all");

    if (openAllBtn) {
        openAllBtn.addEventListener("click", () => {
            document.querySelectorAll(".collapsible").forEach(c => c.classList.add("open"));
        });
    }

    if (closeAllBtn) {
        closeAllBtn.addEventListener("click", () => {
            document.querySelectorAll(".collapsible").forEach(c => c.classList.remove("open"));
        });
    }
}

document.addEventListener("DOMContentLoaded", initCollapsibles);
