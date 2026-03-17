import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(
    page_title="Grizzly et Moineau - Gestion de Saga",
    page_icon="📚",
    layout="wide"
)

html_code = """
<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>Grizzly et Moineau - Gestion de Saga</title>
    <style>
        :root {
            --color-bg-dark: #0f172a;
            --color-bg-elevated: #1e293b;
            --color-bg-surface: #334155;
            --color-text-primary: #f1f5f9;
            --color-text-secondary: #cbd5e1;
            --color-text-muted: #94a3b8;
            --color-accent: #38bdf8;
            --color-accent-hover: #0ea5e9;
            --color-success: #10b981;
            --color-warning: #f59e0b;
            --color-danger: #ef4444;
        }

        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: var(--color-bg-dark);
            color: var(--color-text-primary);
            min-height: 100vh;
        }

        .container {
            max-width: 100%;
            padding: 16px;
        }

        .header {
            background: var(--color-bg-elevated);
            padding: 20px;
            margin-bottom: 20px;
            border-radius: 12px;
            text-align: center;
        }

        .header h1 {
            font-size: 1.75rem;
            margin-bottom: 8px;
            color: var(--color-accent);
        }

        .header p {
            color: var(--color-text-muted);
            font-size: 0.9rem;
        }

        .nav-tabs {
            display: flex;
            gap: 8px;
            margin-bottom: 24px;
            overflow-x: auto;
            padding-bottom: 8px;
        }

        .nav-tab {
            padding: 12px 20px;
            background: var(--color-bg-elevated);
            border: none;
            border-radius: 8px;
            color: var(--color-text-secondary);
            cursor: pointer;
            font-size: 0.95rem;
            white-space: nowrap;
            transition: all 0.3s;
            flex-shrink: 0;
        }

        .nav-tab.active {
            background: var(--color-accent);
            color: var(--color-bg-dark);
            font-weight: 600;
        }

        .nav-tab:hover:not(.active) {
            background: var(--color-bg-surface);
        }

        .section {
            display: none;
        }

        .section.active {
            display: block;
        }

        .card {
            background: var(--color-bg-elevated);
            padding: 20px;
            border-radius: 12px;
            margin-bottom: 16px;
        }

        .card h2 {
            color: var(--color-accent);
            margin-bottom: 16px;
            font-size: 1.5rem;
        }

        .card h3 {
            color: var(--color-text-primary);
            margin-bottom: 12px;
            font-size: 1.2rem;
        }

        .form-group {
            margin-bottom: 16px;
        }

        .form-label {
            display: block;
            margin-bottom: 8px;
            color: var(--color-text-secondary);
            font-weight: 500;
            font-size: 0.9rem;
        }

        .form-control {
            width: 100%;
            padding: 12px;
            background: var(--color-bg-dark);
            border: 2px solid var(--color-bg-surface);
            border-radius: 8px;
            color: var(--color-text-primary);
            font-size: 1rem;
            transition: border-color 0.3s;
        }

        .form-control:focus {
            outline: none;
            border-color: var(--color-accent);
        }

        textarea.form-control {
            min-height: 120px;
            resize: vertical;
            font-family: inherit;
        }

        select.form-control {
            cursor: pointer;
        }

        .btn {
            padding: 14px 24px;
            border: none;
            border-radius: 8px;
            font-size: 1rem;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s;
            width: 100%;
            margin-top: 8px;
        }

        .btn-primary {
            background: var(--color-accent);
            color: var(--color-bg-dark);
        }

        .btn-primary:hover {
            background: var(--color-accent-hover);
        }

        .btn-success {
            background: var(--color-success);
            color: white;
        }

        .btn-danger {
            background: var(--color-danger);
            color: white;
        }

        .character-card {
            background: var(--color-bg-surface);
            padding: 16px;
            border-radius: 8px;
            margin-bottom: 12px;
            border-left: 4px solid var(--color-accent);
        }

        .character-card h4 {
            color: var(--color-accent);
            margin-bottom: 8px;
        }

        .character-card p {
            color: var(--color-text-secondary);
            font-size: 0.9rem;
            margin-bottom: 4px;
        }

        .tag {
            display: inline-block;
            padding: 4px 12px;
            background: var(--color-bg-dark);
            border-radius: 16px;
            font-size: 0.8rem;
            margin-right: 6px;
            margin-top: 6px;
            color: var(--color-text-secondary);
        }

        .tag.tome {
            background: var(--color-accent);
            color: var(--color-bg-dark);
        }

        .tag.trauma {
            background: var(--color-danger);
            color: white;
        }

        .tag.queer {
            background: #ec4899;
            color: white;
        }

        .tag.pouvoir {
            background: #8b5cf6;
            color: white;
        }

        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
            gap: 12px;
            margin-bottom: 20px;
        }

        .stat-card {
            background: var(--color-bg-surface);
            padding: 16px;
            border-radius: 8px;
            text-align: center;
        }

        .stat-value {
            font-size: 2rem;
            font-weight: bold;
            color: var(--color-accent);
        }

        .stat-label {
            font-size: 0.85rem;
            color: var(--color-text-muted);
            margin-top: 4px;
        }

        .analysis-result {
            background: var(--color-bg-surface);
            padding: 16px;
            border-radius: 8px;
            margin-top: 16px;
            display: none;
        }

        .analysis-result.show {
            display: block;
        }

        .export-section {
            margin-top: 20px;
            padding-top: 20px;
            border-top: 2px solid var(--color-bg-surface);
        }

        @media (min-width: 768px) {
            .container {
                max-width: 1200px;
                margin: 0 auto;
                padding: 24px;
            }

            .btn {
                width: auto;
                min-width: 180px;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📚 Grizzly et Moineau</h1>
            <p>Base de données interactive pour votre saga de 6 tomes</p>
        </div>

        <div class="nav-tabs">
            <button class="nav-tab active" onclick="showSection(event, 'dashboard')">Tableau de bord</button>
            <button class="nav-tab" onclick="showSection(event, 'characters')">Base Personnages</button>
            <button class="nav-tab" onclick="showSection(event, 'analysis')">Analyse de Texte</button>
            <button class="nav-tab" onclick="showSection(event, 'explorer')">Explorateur</button>
        </div>

        <div id="dashboard" class="section active">
            <div class="stats-grid">
                <div class="stat-card">
                    <div class="stat-value" id="statsCharacters">7</div>
                    <div class="stat-label">Personnages</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value" id="statsAnalyses">0</div>
                    <div class="stat-label">Analyses</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value">6</div>
                    <div class="stat-label">Tomes</div>
                </div>
            </div>

            <div class="card">
                <h2>Vue d'ensemble</h2>
                <p style="color: var(--color-text-secondary); margin-bottom: 16px;">
                    Bienvenue dans votre outil de gestion de saga. Naviguez entre les sections pour gérer vos personnages, analyser des extraits de texte et explorer votre univers narratif.
                </p>
                <div id="recentAnalyses"></div>
            </div>

            <div class="card export-section">
                <h3>Sauvegarde & Export</h3>
                <button class="btn btn-success" onclick="exportData()">💾 Télécharger les données (JSON)</button>
                <button class="btn btn-primary" onclick="document.getElementById('importFile').click()">📂 Importer des données</button>
                <input type="file" id="importFile" accept=".json" style="display: none;" onchange="importData(event)">
            </div>
        </div>

        <div id="characters" class="section">
            <div class="card">
                <h2>Ajouter un personnage</h2>
                <form id="characterForm">
                    <div class="form-group">
                        <label class="form-label">Nom</label>
                        <input type="text" class="form-control" id="charName" required>
                    </div>
                    <div class="form-group">
                        <label class="form-label">Surnom</label>
                        <input type="text" class="form-control" id="charNickname">
                    </div>
                    <div class="form-group">
                        <label class="form-label">Tomes (séparés par des virgules, ex: 1,2,3)</label>
                        <input type="text" class="form-control" id="charTomes" placeholder="1,2,3">
                    </div>
                    <div class="form-group">
                        <label class="form-label">Physique</label>
                        <textarea class="form-control" id="charPhysique"></textarea>
                    </div>
                    <div class="form-group">
                        <label class="form-label">Psychologie</label>
                        <textarea class="form-control" id="charPsycho"></textarea>
                    </div>
                    <div class="form-group">
                        <label class="form-label">Pouvoirs</label>
                        <input type="text" class="form-control" id="charPouvoirs" placeholder="Ex: fils bleus, aura">
                    </div>
                    <div class="form-group">
                        <label class="form-label">Traumas</label>
                        <textarea class="form-control" id="charTraumas"></textarea>
                    </div>
                    <div class="form-group">
                        <label class="form-label">Liens Queer</label>
                        <textarea class="form-control" id="charQueer"></textarea>
                    </div>
                    <button type="submit" class="btn btn-primary">Ajouter le personnage</button>
                </form>
            </div>

            <div class="card">
                <h2>Liste des personnages</h2>
                <div id="charactersList"></div>
            </div>
        </div>

        <div id="analysis" class="section">
            <div class="card">
                <h2>Analyse de Texte</h2>
                <div class="form-group">
                    <label class="form-label">Collez votre extrait ici</label>
                    <textarea class="form-control" id="textExtract" placeholder="Collez un extrait de votre manuscrit..." style="min-height: 200px;"></textarea>
                </div>
                <button class="btn btn-primary" onclick="analyzeText()">🔍 Analyser l'extrait</button>

                <div id="analysisResult" class="analysis-result">
                    <h3>Résultats de l'analyse</h3>
                    <div id="analysisContent"></div>
                </div>
            </div>

            <div class="card">
                <h2>Historique des analyses</h2>
                <div id="analysisHistory"></div>
            </div>
        </div>

        <div id="explorer" class="section">
            <div class="card">
                <h2>Explorateur de Saga</h2>
                <div class="form-group">
                    <label class="form-label">Filtrer par tome</label>
                    <select class="form-control" id="filterTome" onchange="filterBySaga()">
                        <option value="all">Tous les tomes</option>
                        <option value="1">Tome 1</option>
                        <option value="2">Tome 2</option>
                        <option value="3">Tome 3</option>
                        <option value="4">Tome 4</option>
                        <option value="5">Tome 5</option>
                        <option value="6">Tome 6</option>
                    </select>
                </div>
                <div id="explorerResults"></div>
            </div>
        </div>
    </div>

    <script>
        let characters = [
            {id: 1, name: 'Lo', nickname: '', tomes: [1,2,3,4,5,6], physique: '', psychologie: '', pouvoirs: '', traumas: '', queer: ''},
            {id: 2, name: 'Jonas', nickname: '', tomes: [1,2,3,4,5,6], physique: '', psychologie: '', pouvoirs: '', traumas: '', queer: ''},
            {id: 3, name: 'Zack', nickname: '', tomes: [1,2,3,4,5,6], physique: '', psychologie: '', pouvoirs: '', traumas: '', queer: ''},
            {id: 4, name: 'Jade', nickname: '', tomes: [1,2,3,4,5,6], physique: '', psychologie: '', pouvoirs: '', traumas: '', queer: ''},
            {id: 5, name: 'Autyss', nickname: '', tomes: [1,2,3,4,5,6], physique: '', psychologie: '', pouvoirs: '', traumas: '', queer: ''},
            {id: 6, name: 'Paul', nickname: '', tomes: [1,2,3,4,5,6], physique: '', psychologie: '', pouvoirs: '', traumas: '', queer: ''},
            {id: 7, name: 'Luc', nickname: '', tomes: [1,2,3,4,5,6], physique: '', psychologie: '', pouvoirs: '', traumas: '', queer: ''}
        ];
        
        let analyses = [];

        function loadFromStorage() {
            const savedChars = localStorage.getItem('gmCharacters');
            const savedAnalyses = localStorage.getItem('gmAnalyses');
            if (savedChars) characters = JSON.parse(savedChars);
            if (savedAnalyses) analyses = JSON.parse(savedAnalyses);
        }

        function saveToStorage() {
            localStorage.setItem('gmCharacters', JSON.stringify(characters));
            localStorage.setItem('gmAnalyses', JSON.stringify(analyses));
        }

        function showSection(evt, sectionName) {
            document.querySelectorAll('.section').forEach(s => s.classList.remove('active'));
            document.querySelectorAll('.nav-tab').forEach(t => t.classList.remove('active'));
            document.getElementById(sectionName).classList.add('active');
            if (evt && evt.target) evt.target.classList.add('active');

            if (sectionName === 'characters') {
                displayCharacters();
            } else if (sectionName === 'dashboard') {
                updateDashboard();
                updateRecentAnalyses();
            } else if (sectionName === 'analysis') {
                displayAnalysisHistory();
            } else if (sectionName === 'explorer') {
                filterBySaga();
            }
        }

        function addCharacter(event) {
            event.preventDefault();
            const tomesStr = document.getElementById('charTomes').value;
            const tomes = tomesStr ? tomesStr.split(',').map(t => parseInt(t.trim())).filter(t => t >= 1 && t <= 6) : [];
            const newChar = {
                id: characters.length ? Math.max(...characters.map(c => c.id)) + 1 : 1,
                name: document.getElementById('charName').value,
                nickname: document.getElementById('charNickname').value,
                tomes: tomes,
                physique: document.getElementById('charPhysique').value,
                psychologie: document.getElementById('charPsycho').value,
                pouvoirs: document.getElementById('charPouvoirs').value,
                traumas: document.getElementById('charTraumas').value,
                queer: document.getElementById('charQueer').value
            };
            characters.push(newChar);
            saveToStorage();
            document.getElementById('characterForm').reset();
            displayCharacters();
            updateDashboard();
            alert('Personnage ajouté avec succès !');
        }

        function displayCharacters() {
            const container = document.getElementById('charactersList');
            if (characters.length === 0) {
                container.innerHTML = '<p style="color: var(--color-text-muted);">Aucun personnage enregistré.</p>';
                return;
            }
            container.innerHTML = characters.map(char => `
                <div class="character-card">
                    <h4>${char.name}${char.nickname ? ' "' + char.nickname + '"' : ''}</h4>
                    ${char.tomes.length > 0 ? char.tomes.map(t => `<span class="tag tome">T${t}</span>`).join('') : ''}
                    ${char.physique ? `<p><strong>Physique:</strong> ${char.physique}</p>` : ''}
                    ${char.psychologie ? `<p><strong>Psychologie:</strong> ${char.psychologie}</p>` : ''}
                    ${char.pouvoirs ? `<p><strong>Pouvoirs:</strong> ${char.pouvoirs}</p>` : ''}
                    ${char.traumas ? `<p><strong>Traumas:</strong> ${char.traumas}</p>` : ''}
                    ${char.queer ? `<p><strong>Liens Queer:</strong> ${char.queer}</p>` : ''}
                    <button class="btn btn-danger" onclick="deleteCharacter(${char.id})" style="margin-top: 12px;">Supprimer</button>
                </div>
            `).join('');
        }

        function deleteCharacter(id) {
            if (confirm('Supprimer ce personnage ?')) {
                characters = characters.filter(c => c.id !== id);
                saveToStorage();
                displayCharacters();
                updateDashboard();
            }
        }

        function analyzeText() {
            const text = document.getElementById('textExtract').value.trim();
            if (!text) {
                alert('Veuillez coller un extrait de texte.');
                return;
            }
            const textLower = text.toLowerCase();
            const foundChars = [];
            characters.forEach(char => {
                if (textLower.includes(char.name.toLowerCase())) {
                    foundChars.push(char.name);
                }
            });

            const types = [];
            const keywords = {
                'Trauma': ['trauma', 'peur', 'angoisse', 'souffrance', 'douleur', 'blessure', 'cicatrice'],
                'Relation Queer': ['amour', 'aimer', 'relation', 'couple', 'baiser', 'embrasser', 'tendresse'],
                'Réseau': ['réseau', 'connexion', 'lien', 'fils', 'trame', 'toile'],
                'Pouvoir': ['pouvoir', 'aura', 'fils bleus', 'capacité', 'don', 'magie'],
                'Objet': ['objet', 'artefact', 'symbole', 'talisman']
            };
            for (const [type, tags] of Object.entries(keywords)) {
                if (tags.some(tag => textLower.includes(tag))) {
                    types.push(type);
                }
            }

            const result = {
                id: Date.now(),
                date: new Date().toLocaleString('fr-CA'),
                text: text.substring(0, 200) + (text.length > 200 ? '...' : ''),
                characters: foundChars,
                types: types
            };
            analyses.unshift(result);
            saveToStorage();
            displayAnalysisResult(result);
            displayAnalysisHistory();
            updateDashboard();
        }

        function displayAnalysisResult(result) {
            const div = document.getElementById('analysisResult');
            const content = document.getElementById('analysisContent');
            div.classList.add('show');
            content.innerHTML = `
                <p style="color: var(--color-text-secondary); margin-bottom: 12px;">
                    <strong>Extrait analysé :</strong> ${result.text}
                </p>
                <div style="margin-bottom: 12px;">
                    <strong>Personnages détectés :</strong><br>
                    ${result.characters.length > 0 
                        ? result.characters.map(c => `<span class="tag">${c}</span>`).join('') 
                        : '<span class="tag">Aucun</span>'}
                </div>
                <div style="margin-bottom: 12px;">
                    <strong>Types d\'éléments :</strong><br>
                    ${result.types.length > 0
                        ? result.types.map(t => {
                            let className = 'tag';
                            if (t === 'Trauma') className = 'tag trauma';
                            else if (t === 'Relation Queer') className = 'tag queer';
                            else if (t === 'Pouvoir') className = 'tag pouvoir';
                            return `<span class="${className}">${t}</span>`;
                        }).join('')
                        : '<span class="tag">Aucun</span>'}
                </div>
            `;
        }

              function displayAnalysisHistory() {
            const container = document.getElementById('analysisHistory');
            if (analyses.length === 0) {
                container.innerHTML = '<p style="color: var(--color-text-muted);">Aucune analyse enregistrée.</p>';
                return;
            }
            const recent = analyses.slice(0, 20);
            container.innerHTML = recent.map(a => `
                <div class="character-card">
                    <h4>Analyse du ${a.date}</h4>
                    <p style="margin-bottom: 8px;">${a.text}</p>
                    ${a.characters.length ? '<div>' + a.characters.map(c => `<span class="tag">${c}</span>`).join('') + '</div>' : ''}
                </div>
            `).join('');
        }

        function updateDashboard() {
            document.getElementById('statsCharacters').textContent = characters.length;
            document.getElementById('statsAnalyses').textContent = analyses.length;
        }

        function updateRecentAnalyses() {
            const div = document.getElementById('recentAnalyses');
            if (!analyses.length) {
                div.innerHTML = '';
                return;
            }
            const recent = analyses.slice(0, 3);
            div.innerHTML = '<h3>Analyses récentes</h3>' + recent.map(a => `
                <div class="character-card">
                    <h4>Analyse du ${a.date}</h4>
                    <p>${a.text}</p>
                </div>
            `).join('');
        }

        function filterBySaga() {
            const tome = document.getElementById('filterTome').value;
            const container = document.getElementById('explorerResults');
            if (tome === 'all') {
                container.innerHTML = `
                    <div class="character-card">
                        <h4>Tous les personnages</h4>
                        ${characters.map(c => `<span class="tag">${c.name}</span>`).join('')}
                    </div>
                `;
            } else {
                const filtered = characters.filter(c => c.tomes.includes(parseInt(tome)));
                if (!filtered.length) {
                    container.innerHTML = '<p style="color: var(--color-text-muted);">Aucun personnage dans ce tome.</p>';
                } else {
                    container.innerHTML = filtered.map(char => `
                        <div class="character-card">
                            <h4>${char.name}${char.nickname ? ' "' + char.nickname + '"' : ''}</h4>
                            ${char.physique ? `<p><strong>Physique:</strong> ${char.physique}</p>` : ''}
                            ${char.pouvoirs ? `<p><strong>Pouvoirs:</strong> ${char.pouvoirs}</p>` : ''}
                        </div>
                    `).join('');
                }
            }
        }

        function exportData() {
            const data = {
                characters,
                analyses,
                exportDate: new Date().toISOString()
            };
            const blob = new Blob([JSON.stringify(data, null, 2)], {type: 'application/json'});
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `grizzly-moineau-${Date.now()}.json`;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            URL.revokeObjectURL(url);
        }

        function importData(event) {
            const file = event.target.files[0];
            if (!file) return;
            const reader = new FileReader();
            reader.onload = e => {
                try {
                    const data = JSON.parse(e.target.result);
                    if (data.characters) characters = data.characters;
                    if (data.analyses) analyses = data.analyses;
                    saveToStorage();
                    alert('Données importées avec succès !');
                    updateDashboard();
                    displayCharacters();
                    displayAnalysisHistory();
                    updateRecentAnalyses();
                } catch (err) {
                    alert('Erreur lors de l\'import du fichier.');
                }
            };
            reader.readAsText(file);
        }

        // Initialisation
        loadFromStorage();
        updateDashboard();
        displayCharacters();
        displayAnalysisHistory();
        updateRecentAnalyses();

        // Form handler
        document.addEventListener('DOMContentLoaded', () => {
            const form = document.getElementById('characterForm');
            if (form) {
                form.addEventListener('submit', addCharacter);
            }
        });
    </script>
</body>
</html>
"""

components.html(html_code, height=900, scrolling=True)

