DEMO_URN = "urn:li:dataset:(urn:li:dataPlatform:bigquery,oncotwin.progression_scores,PROD)"

DEMO_TOOL_RESULTS = {
    "search": {
        "entities": [
            {
                "urn": DEMO_URN,
                "name": "progression_scores",
                "platform": "BigQuery",
                "description": "De-identified cancer progression predictions by cohort and cell cluster.",
            }
        ]
    },
    "get_entities": {
        "urn": DEMO_URN,
        "owners": ["OncoTwin Bioinformatics"],
        "tags": ["CancerProgression", "Deidentified"],
        "schemaFields": ["patient_key", "stage", "cluster_id", "progression_score", "model_version"],
        "health": {"score": 0.82, "freshness": "PASS", "completeness": "WARN"},
    },
    "get_lineage": {
        "upstream": [
            "gcs://oncotwin-scrna/raw/cohort.h5ad",
            "bigquery://oncotwin.normalized_expression",
            "bigquery://oncotwin.progression_features",
        ],
        "downstream": [
            "vertex-ai://models/oncotwin-progression-v3",
            "cloud-run://oncotwin-api",
            "dashboard://oncotwin-3d",
        ],
    },
}

DEMO_SCATTER = [
    {"x": -3.2, "y": 1.1, "z": 0.3, "cluster": "T-cell", "stage": "Primary", "risk": 0.18},
    {"x": -2.7, "y": 0.7, "z": -0.4, "cluster": "T-cell", "stage": "Primary", "risk": 0.24},
    {"x": 0.8, "y": 2.5, "z": 1.0, "cluster": "Tumor", "stage": "Regional", "risk": 0.56},
    {"x": 1.4, "y": 2.1, "z": 0.4, "cluster": "Tumor", "stage": "Regional", "risk": 0.63},
    {"x": 2.8, "y": -1.4, "z": 1.7, "cluster": "Metastatic", "stage": "Metastatic", "risk": 0.91},
    {"x": 3.2, "y": -0.9, "z": 1.2, "cluster": "Metastatic", "stage": "Metastatic", "risk": 0.86},
    {"x": -0.2, "y": -2.6, "z": -1.0, "cluster": "Myeloid", "stage": "Regional", "risk": 0.48},
    {"x": 0.3, "y": -2.2, "z": -1.4, "cluster": "Myeloid", "stage": "Metastatic", "risk": 0.71},
]

# Synthetic research twin used to drive the interactive 3D scene. Positions are
# normalized scene coordinates, not patient anatomy or clinical measurements.
DEMO_TWIN = {
    "case_id": "SYN-NSCLC-A17",
    "organ": "Lung",
    "assay": "scRNA-seq",
    "research_only": True,
    "cell_count": 14382,
    "cell_types": [
        {"name": "Epithelial", "fraction": 0.38, "color": "#62f6cb"},
        {"name": "T cell", "fraction": 0.25, "color": "#62d9ff"},
        {"name": "Myeloid", "fraction": 0.22, "color": "#ffc76b"},
        {"name": "Tumor-like", "fraction": 0.15, "color": "#ff5d91"},
    ],
    "lesions": [
        {"id": "L1", "label": "Primary focus", "position": [-0.30, 0.46, 0.63], "appears_at": 0, "risk": 0.61},
        {"id": "L2", "label": "Local extension", "position": [0.64, 0.22, 0.60], "appears_at": 1, "risk": 0.73},
        {"id": "L3", "label": "Regional focus", "position": [0.55, -0.60, 0.55], "appears_at": 2, "risk": 0.82},
        {"id": "L4", "label": "Nodal focus", "position": [-0.72, -0.68, 0.48], "appears_at": 3, "risk": 0.91},
        {"id": "L5", "label": "Distant focus", "position": [0.78, 0.78, 0.42], "appears_at": 4, "risk": 0.96},
    ],
    "stages": [
        {"index": 0, "label": "00", "title": "Baseline", "burden": 0.18, "quality": 0.96, "signature": "EPCAM-high epithelial state"},
        {"index": 1, "label": "01", "title": "Stage I", "burden": 0.33, "quality": 0.93, "signature": "Localized proliferative MKI67 signal"},
        {"index": 2, "label": "02", "title": "Stage II", "burden": 0.51, "quality": 0.87, "signature": "Local extension with myeloid transition"},
        {"index": 3, "label": "03", "title": "Stage III", "burden": 0.72, "quality": 0.79, "signature": "Synthetic regional progression state"},
        {"index": 4, "label": "04", "title": "Stage IV", "burden": 0.91, "quality": 0.71, "signature": "Synthetic distant progression state"},
    ],
}

DEMO_COHORTS = [
    {"code": "LUAD", "name": "Lung adenocarcinoma", "assets": 27, "trust": 61, "color": "#ff6f6f", "incident": "RNA-seq freshness breach", "model": "luad_progression_v3", "owner": "Thoracic ML", "source": "TCGA-LUAD + public scRNA atlas", "drivers": [["KRAS", 84], ["TP53", 73], ["STK11", 62]], "composition": [["Epithelial", 18], ["T cells", 21], ["Macrophages", 18], ["Malignant", 43]], "molecules": [["Sotorasib", 91], ["Adagrasib", 87]]},
    {"code": "LIHC", "name": "Hepatocellular carcinoma", "assets": 22, "trust": 74, "color": "#f5aa5c", "incident": "Pathway feature drift", "model": "lihc_survival_v2", "owner": "Hepatic AI", "source": "TCGA-LIHC + HCA liver", "drivers": [["TERT", 79], ["CTNNB1", 71], ["TP53", 65]], "composition": [["Hepatocyte", 31], ["T cells", 19], ["Kupffer", 23], ["Malignant", 27]], "molecules": [["Lenvatinib", 82], ["Sorafenib", 76]]},
    {"code": "PAAD", "name": "Pancreatic adenocarcinoma", "assets": 19, "trust": 69, "color": "#bd83ef", "incident": "Cell annotation gap", "model": "paad_response_v4", "owner": "GI Oncology ML", "source": "TCGA-PAAD + public pancreas atlas", "drivers": [["KRAS", 92], ["TP53", 77], ["SMAD4", 58]], "composition": [["Ductal", 22], ["T cells", 12], ["Fibroblast", 36], ["Malignant", 30]], "molecules": [["Olaparib", 79], ["Erlotinib", 63]]},
    {"code": "KIRC", "name": "Clear-cell renal carcinoma", "assets": 18, "trust": 82, "color": "#70adf5", "incident": "Feature distribution shift", "model": "kirc_risk_v2", "owner": "Renal Data Lab", "source": "TCGA-KIRC + kidney cell atlas", "drivers": [["VHL", 88], ["PBRM1", 68], ["SETD2", 54]], "composition": [["Proximal", 25], ["T cells", 28], ["Myeloid", 19], ["Malignant", 28]], "molecules": [["Belzutifan", 90], ["Axitinib", 81]]},
    {"code": "COAD", "name": "Colorectal adenocarcinoma", "assets": 24, "trust": 57, "color": "#e979ae", "incident": "Breaking schema change", "model": "coad_recurrence_v5", "owner": "GI Biomarkers", "source": "TCGA-COAD + colon cell atlas", "drivers": [["APC", 89], ["TP53", 75], ["KRAS", 69]], "composition": [["Enterocyte", 21], ["T cells", 20], ["Stromal", 24], ["Malignant", 35]], "molecules": [["Cetuximab", 84], ["Encorafenib", 78]]},
    {"code": "SKCM", "name": "Cutaneous melanoma", "assets": 21, "trust": 78, "color": "#7eddb5", "incident": "Model endpoint stale", "model": "skcm_response_v3", "owner": "Dermato-oncology AI", "source": "TCGA-SKCM + melanoma atlas", "drivers": [["BRAF", 86], ["NRAS", 67], ["NF1", 51]], "composition": [["Melanocyte", 16], ["T cells", 34], ["Myeloid", 18], ["Malignant", 32]], "molecules": [["Dabrafenib", 93], ["Trametinib", 89]]},
    {"code": "GBM", "name": "Glioblastoma", "assets": 20, "trust": 64, "color": "#c985df", "incident": "Dataset owner missing", "model": "gbm_state_v2", "owner": "Neuro-oncology ML", "source": "TCGA-GBM + brain tumor atlas", "drivers": [["EGFR", 83], ["PTEN", 66], ["TP53", 59]], "composition": [["Neural", 18], ["T cells", 8], ["Microglia", 29], ["Malignant", 45]], "molecules": [["Temozolomide", 81], ["Osimertinib", 67]]},
]
