"""
SASTRA Research Finder - Configuration Module
Contains all configuration constants and settings.
"""

import os
from pathlib import Path
from typing import Dict, List, Set, Optional
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings."""

    # API Settings
    APP_NAME: str = "SASTRA Research Finder"
    APP_VERSION: str = "4.0.0"
    DEBUG: bool = False
    PORT: int = 8000

    # Public URL of this backend (used to build absolute static asset URLs
    # like staff photo links so the frontend on a different origin can load them).
    # Set to e.g. "https://<user>-<space>.hf.space" on HuggingFace Spaces.
    BACKEND_PUBLIC_URL: str = ""

    # CORS Settings — comma-separated string. In production, set CORS_ORIGINS
    # env var to include your Vercel domain.
    # NOTE: stored as `str` (not `List[str]`) because pydantic-settings tries to
    # JSON-decode List env vars before our validator can split the CSV.
    CORS_ORIGINS: str = "http://localhost:3000,http://localhost:5173"
    
    # Database Settings (MongoDB)
    MONGODB_URL: str = "mongodb://localhost:27017"
    DATABASE_NAME: str = "sastra_research"
    
    # SQLite Database (for new features)
    SQLALCHEMY_DATABASE_URL: str = "sqlite:///./data/sastra.db"
    
    # File Paths
    BASE_DIR: Path = Path(__file__).parent.parent.parent
    DATA_DIR: Path = BASE_DIR / "data"
    CACHE_DIR: Path = DATA_DIR / "cache"
    EXCEL_FILE: Path = DATA_DIR / "SASTRA_Publications_2024-25.xlsx"
    FACULTY_FILE: Path = DATA_DIR / "Faculty-List.xlsx"
    
    # Embedding Model Configuration
    EMBEDDING_MODEL: str = "all-MiniLM-L6-v2"
    EMBEDDING_DIMENSION: int = 384
    
    # Search Configuration
    MAX_SEARCH_RESULTS: int = 100
    MAX_RAG_CONTEXT: int = 20
    SEMANTIC_SEARCH_TOP_K: int = 50
    
    # Mistral AI Configuration
    MISTRAL_API_KEY: str = ""
    MISTRAL_MODEL: str = "mistral-small-latest"

    # Exa AI Search Configuration
    EXA_API_KEY: Optional[str] = None

    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=True,
        extra="ignore",
    )

    @property
    def cors_origins_list(self) -> List[str]:
        """Parse CORS_ORIGINS comma-separated string into a list at use site."""
        return [item.strip() for item in self.CORS_ORIGINS.split(",") if item.strip()]

    @field_validator("BACKEND_PUBLIC_URL", mode="before")
    @classmethod
    def _strip_backend_url(cls, value):
        """Trim trailing slash so we can compose URLs cleanly."""
        if isinstance(value, str):
            return value.strip().rstrip("/")
        return ""

    @field_validator("DEBUG", mode="before")
    @classmethod
    def _parse_debug(cls, value):
        """Parse DEBUG robustly from env strings."""
        if isinstance(value, bool):
            return value
        if isinstance(value, str):
            normalized = value.strip().lower()
            if normalized in {"1", "true", "yes", "on"}:
                return True
            if normalized in {"0", "false", "no", "off", "release"}:
                return False
        return False

    @field_validator("MISTRAL_API_KEY", mode="before")
    @classmethod
    def _strip_mistral_key(cls, value):
        """Trim accidental whitespace from API key values."""
        if isinstance(value, str):
            return value.strip()
        return ""


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


# =============================================================================
# SASTRA SCHOOLS MAPPING
# =============================================================================
SASTRA_SCHOOLS: Dict[str, List[str]] = {
    "School of Computing": ["computing", "computer science", "information technology", "software", "it dept"],
    "School of Electrical & Electronics Engineering": ["electrical", "electronics", "eee", "power systems"],
    "School of Mechanical Engineering": ["mechanical", "manufacturing", "thermal", "mechatronics"],
    "School of Civil Engineering": ["civil", "structural", "construction", "environmental engineering"],
    "School of Chemical & Biotechnology": ["chemical", "biotechnology", "biotech", "biochem"],
    "School of Humanities & Sciences": ["humanities", "sciences", "physics", "chemistry", "mathematics"],
    "School of Management": ["management", "business", "mba", "commerce"],
    "School of Law": ["law", "legal"],
    "School of Education": ["education", "pedagogy"],
}

# =============================================================================
# DOCUMENT TYPE MAPPING
# =============================================================================
DOCUMENT_TYPES: Dict[str, str] = {
    "Article": "Journal Article",
    "Conference Paper": "Conference Paper",
    "Book Chapter": "Book Chapter",
    "Review": "Review Article",
    "Book": "Book",
    "Editorial": "Editorial",
    "Erratum": "Erratum",
    "Letter": "Letter",
    "Note": "Note",
    "Short Survey": "Short Survey",
    "Retracted": "Retracted",
}

# =============================================================================
# COUNTRY PATTERNS FOR AFFILIATION PARSING
# =============================================================================
COUNTRY_PATTERNS: List[str] = [
    r'\bIndia\b', r'\bUSA\b', r'\bUnited States\b', r'\bUK\b', r'\bUnited Kingdom\b',
    r'\bChina\b', r'\bJapan\b', r'\bGermany\b', r'\bFrance\b', r'\bCanada\b',
    r'\bAustralia\b', r'\bSingapore\b', r'\bMalaysia\b', r'\bThailand\b',
    r'\bSouth Korea\b', r'\bKorea\b', r'\bNetherlands\b', r'\bSweden\b',
    r'\bSwitzerland\b', r'\bItaly\b', r'\bSpain\b', r'\bBrazil\b', r'\bMexico\b',
    r'\bRussia\b', r'\bSouth Africa\b', r'\bEgypt\b', r'\bSaudi Arabia\b', r'\bUAE\b',
    r'\bUnited Arab Emirates\b', r'\bNew Zealand\b', r'\bIreland\b', r'\bBelgium\b',
    r'\bAustria\b', r'\bDenmark\b', r'\bNorway\b', r'\bFinland\b', r'\bPoland\b',
    r'\bTurkey\b', r'\bIran\b', r'\bPakistan\b', r'\bBangladesh\b', r'\bSri Lanka\b',
    r'\bNepal\b', r'\bIndonesia\b', r'\bPhilippines\b', r'\bVietnam\b', r'\bIsrael\b',
    r'\bGreece\b', r'\bPortugal\b', r'\bTaiwan\b', r'\bHong Kong\b', r'\bQatar\b',
    r'\bKuwait\b', r'\bOman\b', r'\bBahrain\b', r'\bJordan\b', r'\bLebanon\b',
]

# =============================================================================
# STOPWORDS FOR KEYWORD EXTRACTION
# =============================================================================
STOPWORDS: Set[str] = {
    'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
    'of', 'with', 'by', 'from', 'as', 'is', 'was', 'are', 'were', 'been',
    'be', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would',
    'could', 'should', 'may', 'might', 'must', 'shall', 'can', 'need',
    'this', 'that', 'these', 'those', 'it', 'its', 'which', 'who', 'whom',
    'what', 'when', 'where', 'why', 'how', 'all', 'each', 'every', 'both',
    'few', 'more', 'most', 'other', 'some', 'such', 'no', 'nor', 'not',
    'only', 'own', 'same', 'so', 'than', 'too', 'very', 'just', 'also',
    'into', 'through', 'during', 'before', 'after', 'above', 'below',
    'between', 'under', 'again', 'further', 'then', 'once', 'here', 'there',
    'any', 'about', 'because', 'while', 'being', 'having', 'using', 'used',
    'shows', 'shown', 'show', 'based', 'however', 'therefore', 'thus',
    'paper', 'study', 'research', 'result', 'results', 'method', 'approach',
    'proposed', 'work', 'article', 'present', 'presents', 'presented',
    'obtained', 'achieved', 'performs', 'performance', 'various', 'different',
    'new', 'novel', 'several', 'many', 'first', 'second', 'third', 'one',
    'two', 'three', 'four', 'five', 'high', 'low', 'large', 'small',
    'important', 'significant', 'recently', 'mainly', 'particularly',
    'including', 'without', 'among', 'within', 'across', 'along', 'around',
    'upon', 'well', 'still', 'found', 'make', 'made', 'like', 'over',
    'even', 'use', 'uses', 'due', 'via', 'per', 'etc',
}

# =============================================================================
# THEMATIC AREAS - 100 Research Domains
# =============================================================================
THEMATIC_AREAS: Dict[str, List[str]] = {
    # ===== CORE AI & MACHINE LEARNING (8 areas) =====
    'Machine Learning': [
        'machine learning', 'ml', 'supervised learning', 'unsupervised learning',
        'classification', 'regression', 'clustering', 'random forest', 'svm',
        'support vector machine', 'decision tree', 'xgboost', 'ensemble learning',
        'semi-supervised', 'active learning'
    ],
    'Deep Learning': [
        'deep learning', 'neural network', 'cnn', 'convolutional neural', 'rnn',
        'recurrent neural', 'lstm', 'gru', 'transformer', 'attention mechanism',
        'bert', 'gpt', 'resnet', 'vgg', 'u-net', 'unet', 'gan', 'autoencoder',
        'generative adversarial', 'variational autoencoder'
    ],
    'Reinforcement Learning': [
        'reinforcement learning', 'q-learning', 'deep q-network', 'dqn', 'policy gradient',
        'actor-critic', 'reward function', 'markov decision', 'temporal difference',
        'multi-agent learning', 'deep reinforcement'
    ],
    'Transfer Learning': [
        'transfer learning', 'domain adaptation', 'pre-trained model', 'fine-tuning',
        'knowledge transfer', 'zero-shot learning', 'few-shot learning', 'meta-learning'
    ],
    'Explainable AI': [
        'explainable ai', 'interpretable machine learning', 'xai', 'model interpretability',
        'feature importance', 'lime', 'shap', 'attention visualization', 'explainability'
    ],
    'Federated Learning': [
        'federated learning', 'distributed learning', 'privacy-preserving ml',
        'edge learning', 'decentralized learning', 'collaborative learning'
    ],
    'Computer Vision': [
        'computer vision', 'image processing', 'object detection', 'image classification',
        'segmentation', 'face recognition', 'ocr', 'optical character', 'yolo',
        'image analysis', 'feature detection', 'edge detection', 'semantic segmentation',
        'instance segmentation', 'image enhancement', 'super resolution'
    ],
    'Natural Language Processing': [
        'nlp', 'natural language processing', 'text mining', 'sentiment analysis',
        'text classification', 'named entity recognition', 'ner', 'language model',
        'word embedding', 'text analytics', 'topic modeling', 'machine translation',
        'question answering', 'text generation', 'chatbot'
    ],

    # ===== DATA SCIENCE & ANALYTICS (5 areas) =====
    'Data Science & Analytics': [
        'data mining', 'data analysis', 'big data', 'analytics', 'data science',
        'predictive analytics', 'business intelligence', 'data visualization',
        'statistical analysis', 'pattern recognition', 'exploratory data analysis'
    ],
    'Time Series Analysis': [
        'time series', 'forecasting', 'arima', 'seasonal', 'trend analysis',
        'temporal', 'prediction', 'timeseries', 'lstm forecasting', 'prophet',
        'time series decomposition'
    ],
    'Recommender Systems': [
        'recommendation system', 'collaborative filtering', 'content-based filtering',
        'matrix factorization', 'personalization', 'user preference'
    ],
    'Graph Analytics': [
        'graph neural network', 'knowledge graph', 'graph mining', 'network analysis',
        'social network analysis', 'link prediction', 'node classification'
    ],
    'Information Retrieval': [
        'information retrieval', 'search engine', 'document retrieval', 'indexing',
        'ranking algorithm', 'relevance feedback', 'query processing'
    ],

    # ===== HEALTHCARE & BIOMEDICAL (6 areas) =====
    'Medical Imaging': [
        'medical imaging', 'mri', 'ct scan', 'x-ray', 'ultrasound', 'mammography',
        'medical image analysis', 'radiology', 'pathology', 'histopathology'
    ],
    'Healthcare Analytics': [
        'healthcare', 'clinical', 'patient', 'diagnosis', 'prognosis', 'ehr',
        'electronic health record', 'hospital', 'health informatics', 'telemedicine'
    ],
    'Drug Discovery': [
        'drug discovery', 'pharmaceutical', 'drug design', 'molecular docking',
        'compound screening', 'pharmacology', 'drug repurposing'
    ],
    'Bioinformatics': [
        'bioinformatics', 'genomics', 'proteomics', 'gene expression', 'dna',
        'rna', 'sequence analysis', 'protein structure', 'computational biology'
    ],
    'Wearable Health Technology': [
        'wearable', 'health monitoring', 'fitness tracker', 'smartwatch',
        'physiological monitoring', 'vital signs', 'remote monitoring'
    ],
    'Mental Health AI': [
        'mental health', 'depression detection', 'anxiety', 'stress detection',
        'psychological', 'cognitive assessment', 'behavioral analysis'
    ],

    # ===== CYBERSECURITY & PRIVACY (4 areas) =====
    'Cybersecurity': [
        'cybersecurity', 'intrusion detection', 'malware', 'network security',
        'threat detection', 'vulnerability', 'attack detection', 'cyber attack'
    ],
    'Privacy & Data Protection': [
        'privacy', 'data protection', 'anonymization', 'differential privacy',
        'gdpr', 'privacy-preserving', 'data encryption'
    ],
    'Blockchain & Distributed Ledger': [
        'blockchain', 'cryptocurrency', 'smart contract', 'distributed ledger',
        'consensus algorithm', 'decentralized', 'ethereum', 'bitcoin'
    ],
    'Network Security': [
        'network security', 'firewall', 'ids', 'ips', 'vpn', 'ddos',
        'penetration testing', 'network monitoring'
    ],

    # ===== IOT & EDGE COMPUTING (4 areas) =====
    'Internet of Things': [
        'iot', 'internet of things', 'sensor network', 'smart home',
        'smart city', 'embedded systems', 'wireless sensor', 'mqtt'
    ],
    'Edge Computing': [
        'edge computing', 'fog computing', 'edge ai', 'mobile edge',
        'distributed computing', 'edge device', 'edge intelligence'
    ],
    'Smart Agriculture': [
        'smart agriculture', 'precision farming', 'crop monitoring',
        'agricultural iot', 'plant disease', 'soil monitoring'
    ],
    'Wireless Communication': [
        'wireless', '5g', 'lte', 'wifi', 'bluetooth', 'zigbee',
        'mobile communication', 'spectrum', 'mimo'
    ],

    # ===== ENERGY & ENVIRONMENT (5 areas) =====
    'Renewable Energy': [
        'renewable energy', 'solar energy', 'wind energy', 'photovoltaic', 'solar cell',
        'wind turbine', 'hydropower', 'biomass', 'green energy', 'sustainable energy'
    ],
    'Power Systems': [
        'power system', 'smart grid', 'power grid', 'electrical grid', 'power flow',
        'load forecasting', 'power quality', 'voltage stability', 'power electronics'
    ],
    'Energy Storage': [
        'energy storage', 'battery', 'lithium-ion', 'supercapacitor', 'fuel cell',
        'hydrogen storage', 'electrochemical', 'battery management'
    ],
    'Environmental Engineering': [
        'environmental', 'pollution', 'air quality', 'water quality', 'waste management',
        'climate change', 'carbon emission', 'sustainability', 'eco-friendly'
    ],
    'Electric Vehicles': [
        'electric vehicle', 'ev', 'hybrid vehicle', 'charging station', 'battery electric',
        'vehicle-to-grid', 'autonomous vehicle', 'self-driving'
    ],

    # ===== MATERIALS & MANUFACTURING (5 areas) =====
    'Materials Science': [
        'materials science', 'nanomaterials', 'composite materials', 'polymer',
        'ceramic', 'alloy', 'thin film', 'coating', 'surface engineering'
    ],
    'Nanotechnology': [
        'nanotechnology', 'nanoparticle', 'nanowire', 'nanotube', 'quantum dot',
        'nanoscale', 'nano-fabrication', 'nano-sensor'
    ],
    'Additive Manufacturing': [
        '3d printing', 'additive manufacturing', 'rapid prototyping', 'selective laser',
        'fused deposition', 'powder bed fusion', 'metal printing'
    ],
    'Robotics & Automation': [
        'robotics', 'robot', 'automation', 'industrial robot', 'manipulator',
        'motion planning', 'robot control', 'human-robot interaction'
    ],
    'Control Systems': [
        'control system', 'pid controller', 'adaptive control', 'optimal control',
        'fuzzy control', 'model predictive control', 'feedback control'
    ],

    # ===== SIGNAL PROCESSING & COMMUNICATIONS (4 areas) =====
    'Signal Processing': [
        'signal processing', 'digital signal', 'filter design', 'fft', 'wavelet',
        'spectral analysis', 'noise reduction', 'signal enhancement'
    ],
    'Speech & Audio Processing': [
        'speech recognition', 'speech synthesis', 'voice', 'audio processing',
        'speaker recognition', 'acoustic', 'music information retrieval'
    ],
    'Image & Video Processing': [
        'video processing', 'video analysis', 'video compression', 'motion detection',
        'video surveillance', 'action recognition', 'video segmentation'
    ],
    'Radar & Remote Sensing': [
        'radar', 'remote sensing', 'satellite imagery', 'sar', 'lidar',
        'hyperspectral', 'geospatial', 'gis'
    ],

    # ===== OPTIMIZATION & OPERATIONS (4 areas) =====
    'Optimization Algorithms': [
        'optimization', 'genetic algorithm', 'particle swarm', 'simulated annealing',
        'ant colony', 'evolutionary algorithm', 'metaheuristic', 'linear programming'
    ],
    'Operations Research': [
        'operations research', 'scheduling', 'resource allocation', 'logistics',
        'supply chain', 'inventory management', 'queueing theory'
    ],
    'Financial Analytics': [
        'financial', 'stock market', 'portfolio', 'risk management', 'trading',
        'cryptocurrency', 'fintech', 'credit scoring', 'fraud detection'
    ],
    'Digital Twin': [
        'digital twin', 'virtual model', 'simulation model', 'cyber-physical system',
        'industry 4.0', 'predictive maintenance'
    ],

    # ===== CLOUD & DISTRIBUTED SYSTEMS (3 areas) =====
    'Cloud Computing': [
        'cloud computing', 'cloud service', 'saas', 'paas', 'iaas', 'virtualization',
        'docker', 'kubernetes', 'microservices', 'serverless', 'cloud-native'
    ],
    'Distributed Systems': [
        'distributed systems', 'distributed computing', 'parallel computing',
        'load balancing', 'fault tolerance', 'replication', 'consistency',
        'mapreduce', 'hadoop', 'spark', 'distributed database'
    ],
    'High-Performance Computing': [
        'high performance computing', 'hpc', 'supercomputer', 'gpu computing',
        'parallel processing', 'cuda', 'opencl', 'mpi', 'cluster computing'
    ],

    # ===== SOFTWARE ENGINEERING (3 areas) =====
    'Software Engineering': [
        'software engineering', 'software development', 'agile', 'devops',
        'software architecture', 'design pattern', 'code quality', 'refactoring',
        'software maintenance', 'continuous integration'
    ],
    'Software Testing & Quality': [
        'software testing', 'test automation', 'quality assurance', 'mutation testing',
        'regression testing', 'code coverage', 'static analysis', 'fault localization',
        'bug detection', 'software reliability'
    ],
    'Human-Computer Interaction': [
        'human-computer interaction', 'hci', 'user interface', 'user experience',
        'usability', 'accessibility', 'gesture recognition', 'eye tracking',
        'interaction design', 'haptic', 'brain-computer interface'
    ],

    # ===== STRUCTURAL & CIVIL ENGINEERING (4 areas) =====
    'Structural Engineering': [
        'structural engineering', 'structural analysis', 'finite element', 'concrete',
        'steel structure', 'seismic', 'earthquake', 'structural health monitoring',
        'bridge', 'structural design', 'load bearing'
    ],
    'Geotechnical Engineering': [
        'geotechnical', 'soil mechanics', 'foundation', 'slope stability', 'landslide',
        'ground improvement', 'tunneling', 'retaining wall', 'bearing capacity'
    ],
    'Transportation Engineering': [
        'transportation', 'traffic', 'highway', 'pavement', 'road safety',
        'traffic flow', 'vehicle routing', 'intelligent transportation',
        'public transport', 'traffic congestion'
    ],
    'Water Resources Engineering': [
        'water resources', 'hydrology', 'groundwater', 'watershed', 'irrigation',
        'flood', 'dam', 'river', 'hydraulic', 'stormwater', 'water treatment'
    ],

    # ===== VLSI & EMBEDDED SYSTEMS (3 areas) =====
    'VLSI Design': [
        'vlsi', 'integrated circuit', 'cmos', 'asic', 'system-on-chip', 'soc',
        'logic design', 'digital circuit', 'low power design', 'chip design'
    ],
    'Embedded Systems': [
        'embedded system', 'microcontroller', 'arm', 'rtos', 'real-time system',
        'firmware', 'arduino', 'raspberry pi', 'system design', 'soc design'
    ],
    'FPGA & Reconfigurable Computing': [
        'fpga', 'reconfigurable', 'hardware accelerator', 'xilinx', 'verilog',
        'vhdl', 'hardware description', 'programmable logic', 'synthesis'
    ],

    # ===== BIOMEDICAL ENGINEERING (3 areas) =====
    'Biomedical Sensors': [
        'biomedical sensor', 'biosensor', 'electrochemical sensor', 'glucose sensor',
        'piezoelectric', 'bioelectronics', 'lab-on-chip', 'point-of-care',
        'implantable sensor', 'bioimpedance'
    ],
    'Tissue Engineering': [
        'tissue engineering', 'scaffold', 'biomaterial', 'biocompatible',
        'cell culture', 'regenerative medicine', 'bioprinting', 'hydrogel',
        'stem cell', 'organ-on-chip'
    ],
    'Prosthetics & Rehabilitation': [
        'prosthetic', 'rehabilitation', 'exoskeleton', 'assistive technology',
        'motion analysis', 'gait analysis', 'physiotherapy', 'orthopedic',
        'artificial limb', 'disability'
    ],

    # ===== MATHEMATICAL SCIENCES (4 areas) =====
    'Mathematical Modeling': [
        'mathematical model', 'mathematical modeling', 'differential equation',
        'dynamical system', 'bifurcation', 'stability analysis', 'epidemic model',
        'compartmental model', 'population dynamics'
    ],
    'Numerical Methods': [
        'numerical method', 'finite difference', 'finite volume', 'boundary element',
        'numerical simulation', 'iterative method', 'convergence analysis',
        'interpolation', 'quadrature', 'numerical solution'
    ],
    'Combinatorics & Graph Theory': [
        'combinatorics', 'graph theory', 'graph coloring', 'matching',
        'domination', 'labeling', 'ramsey', 'extremal graph', 'hypergraph',
        'algebraic graph theory', 'chromatic number'
    ],
    'Stochastic Processes': [
        'stochastic', 'probability', 'markov chain', 'random process',
        'brownian motion', 'poisson process', 'queueing', 'stochastic differential',
        'monte carlo', 'bayesian', 'random walk'
    ],

    # ===== PHYSICS & PHOTONICS (4 areas) =====
    'Optical Engineering & Photonics': [
        'optical', 'photonics', 'fiber optic', 'laser', 'optical fiber',
        'optical sensor', 'optical communication', 'nonlinear optics',
        'waveguide', 'optical amplifier', 'photonic crystal'
    ],
    'Quantum Computing': [
        'quantum computing', 'quantum algorithm', 'qubit', 'quantum gate',
        'quantum entanglement', 'quantum cryptography', 'quantum machine learning',
        'quantum error correction', 'quantum simulation'
    ],
    'Semiconductor Devices': [
        'semiconductor', 'transistor', 'diode', 'mosfet', 'bandgap',
        'doping', 'carrier mobility', 'photodiode', 'solar cell',
        'light emitting diode', 'led', 'heterostructure'
    ],
    'Condensed Matter Physics': [
        'condensed matter', 'solid state', 'crystal structure', 'magnetic',
        'ferroelectric', 'superconductor', 'lattice', 'phonon', 'spintronics',
        'topological insulator', 'phase transition'
    ],

    # ===== CHEMISTRY (4 areas) =====
    'Organic Chemistry': [
        'organic chemistry', 'organic synthesis', 'heterocyclic', 'aromatic',
        'stereochemistry', 'asymmetric synthesis', 'green chemistry',
        'organometallic', 'coupling reaction', 'functional group'
    ],
    'Analytical Chemistry': [
        'analytical chemistry', 'spectroscopy', 'chromatography', 'hplc',
        'mass spectrometry', 'electroanalytical', 'voltammetry', 'titration',
        'uv-vis', 'fluorescence', 'raman spectroscopy'
    ],
    'Catalysis & Reaction Engineering': [
        'catalysis', 'catalyst', 'photocatalysis', 'electrocatalysis',
        'heterogeneous catalysis', 'homogeneous catalysis', 'reaction kinetics',
        'chemical reactor', 'reaction mechanism', 'nanocatalyst'
    ],
    'Chemical Process Engineering': [
        'chemical process', 'process optimization', 'distillation', 'extraction',
        'separation process', 'heat exchanger', 'process simulation',
        'process control', 'chemical plant', 'mass transfer'
    ],

    # ===== EDUCATION & PEDAGOGY (3 areas) =====
    'Educational Technology': [
        'educational technology', 'e-learning', 'online learning', 'mooc',
        'learning management', 'gamification', 'adaptive learning',
        'educational data mining', 'learning analytics', 'blended learning'
    ],
    'STEM Education': [
        'stem education', 'engineering education', 'science education',
        'mathematics education', 'pedagogy', 'curriculum design',
        'student performance', 'assessment', 'academic performance'
    ],
    'Natural Language Understanding': [
        'natural language understanding', 'dialogue system', 'conversational ai',
        'intent recognition', 'slot filling', 'discourse analysis',
        'semantic parsing', 'knowledge base', 'common sense reasoning'
    ],

    # ===== MANAGEMENT & ECONOMICS (3 areas) =====
    'Human Resource Analytics': [
        'human resource', 'employee', 'workforce', 'talent management',
        'organizational behavior', 'job satisfaction', 'workplace',
        'performance appraisal', 'recruitment'
    ],
    'Marketing Analytics': [
        'marketing', 'consumer behavior', 'brand', 'customer satisfaction',
        'market segmentation', 'digital marketing', 'social media marketing',
        'advertising', 'purchase intention'
    ],
    'Entrepreneurship & Innovation': [
        'entrepreneurship', 'innovation', 'startup', 'technology transfer',
        'intellectual property', 'patent', 'commercialization',
        'business model', 'venture capital'
    ],

    # ===== ADVANCED NETWORKING (3 areas) =====
    'Optical Networks': [
        'optical network', 'wavelength division', 'wdm', 'optical switching',
        'optical routing', 'fiber network', 'dwdm', 'all-optical network'
    ],
    'Ad Hoc & Sensor Networks': [
        'ad hoc network', 'manet', 'vanet', 'mesh network', 'routing protocol',
        'sensor network', 'delay tolerant', 'mobile ad hoc', 'cognitive radio'
    ],
    'Software-Defined Networking': [
        'software-defined networking', 'sdn', 'network function virtualization',
        'nfv', 'openflow', 'network slicing', 'programmable network'
    ],

    # ===== THERMAL & FLUID ENGINEERING (3 areas) =====
    'Computational Fluid Dynamics': [
        'computational fluid dynamics', 'cfd', 'navier-stokes', 'turbulence',
        'fluid flow', 'aerodynamics', 'flow simulation', 'reynolds number',
        'boundary layer', 'vortex'
    ],
    'Heat Transfer Engineering': [
        'heat transfer', 'thermal conductivity', 'convection', 'radiation',
        'heat sink', 'thermal management', 'boiling', 'condensation',
        'nanofluid', 'heat pipe'
    ],
    'Microfluidics': [
        'microfluidics', 'lab on chip', 'droplet', 'microchannel',
        'microreactor', 'micro total analysis', 'digital microfluidics',
        'paper-based microfluidics'
    ],

    # ===== AGRICULTURE & FOOD SCIENCE (2 areas) =====
    'Food Science & Technology': [
        'food science', 'food processing', 'food safety', 'food quality',
        'food preservation', 'nutraceutical', 'food packaging',
        'fermentation', 'food additive', 'antioxidant'
    ],
    'Crop Science & Plant Biology': [
        'crop science', 'plant biology', 'plant pathology', 'seed',
        'germination', 'photosynthesis', 'plant growth', 'herbicide',
        'pesticide', 'plant breeding', 'agronomy'
    ],

    # ===== SOCIAL & COMPUTATIONAL (3 areas) =====
    'Social Media Analytics': [
        'social media', 'twitter', 'facebook', 'instagram', 'online community',
        'viral', 'social influence', 'opinion mining', 'fake news detection',
        'misinformation', 'hate speech detection'
    ],
    'Computational Social Science': [
        'computational social', 'social simulation', 'agent-based model',
        'network science', 'community detection', 'influence propagation',
        'information diffusion', 'collective behavior'
    ],
    'Legal Informatics': [
        'legal informatics', 'legal text', 'court judgment', 'legal reasoning',
        'legal nlp', 'contract analysis', 'regulatory compliance',
        'legal analytics', 'judicial decision'
    ],

    # ===== EMERGING TECHNOLOGIES (4 areas) =====
    'Augmented & Virtual Reality': [
        'augmented reality', 'virtual reality', 'mixed reality', 'ar', 'vr',
        '3d visualization', 'immersive', 'head-mounted display', 'hologram',
        'spatial computing'
    ],
    'Autonomous Systems': [
        'autonomous', 'unmanned aerial', 'drone', 'uav', 'path planning',
        'obstacle avoidance', 'autonomous navigation', 'swarm intelligence',
        'multi-robot', 'autonomous driving'
    ],
    'Generative AI': [
        'generative ai', 'large language model', 'llm', 'diffusion model',
        'text-to-image', 'stable diffusion', 'prompt engineering',
        'foundation model', 'gpt', 'image generation'
    ],
    'Ethical AI & AI Governance': [
        'ethical ai', 'ai ethics', 'fairness', 'bias detection', 'algorithmic bias',
        'responsible ai', 'ai governance', 'ai regulation', 'trustworthy ai',
        'ai safety', 'ai accountability'
    ],

    # ===== MISCELLANEOUS ENGINEERING (4 areas) =====
    'Corrosion Science': [
        'corrosion', 'corrosion resistance', 'electrochemical corrosion',
        'protective coating', 'galvanic corrosion', 'pitting corrosion',
        'corrosion inhibitor', 'anti-corrosion'
    ],
    'Tribology': [
        'tribology', 'friction', 'wear', 'lubrication', 'surface roughness',
        'bearing', 'contact mechanics', 'erosion', 'abrasion'
    ],
    'Acoustics & Vibration': [
        'acoustic', 'vibration', 'noise control', 'sound', 'modal analysis',
        'structural vibration', 'noise reduction', 'ultrasonic',
        'vibration damping', 'resonance'
    ],
    'Reliability Engineering': [
        'reliability', 'failure analysis', 'fatigue', 'fracture mechanics',
        'lifetime prediction', 'accelerated testing', 'weibull analysis',
        'mean time between failure', 'mtbf', 'risk assessment'
    ],
}

# =============================================================================
# INTERDISCIPLINARY COMBINATIONS
# =============================================================================
INTERDISCIPLINARY_COMBINATIONS: List[tuple] = [
    # Healthcare + AI
    ('Machine Learning', 'Medical Imaging'),
    ('Deep Learning', 'Medical Imaging'),
    ('Computer Vision', 'Medical Imaging'),
    ('Deep Learning', 'Healthcare Analytics'),
    ('Machine Learning', 'Healthcare Analytics'),
    ('Deep Learning', 'Drug Discovery'),
    ('Machine Learning', 'Bioinformatics'),
    ('Natural Language Processing', 'Healthcare Analytics'),

    # IoT + Analytics
    ('Internet of Things', 'Machine Learning'),
    ('Internet of Things', 'Edge Computing'),
    ('Internet of Things', 'Deep Learning'),
    ('Internet of Things', 'Data Science & Analytics'),

    # Security + AI
    ('Cybersecurity', 'Machine Learning'),
    ('Cybersecurity', 'Deep Learning'),
    ('Privacy & Data Protection', 'Machine Learning'),
    ('Blockchain & Distributed Ledger', 'Cybersecurity'),

    # Energy + AI
    ('Machine Learning', 'Renewable Energy'),
    ('Deep Learning', 'Renewable Energy'),
    ('Machine Learning', 'Power Systems'),
    ('Time Series Analysis', 'Renewable Energy'),

    # Manufacturing + AI
    ('Machine Learning', 'Robotics & Automation'),
    ('Deep Learning', 'Robotics & Automation'),
    ('Computer Vision', 'Robotics & Automation'),
    ('Reinforcement Learning', 'Robotics & Automation'),

    # NLP + Applications
    ('Natural Language Processing', 'Healthcare Analytics'),
    ('Natural Language Processing', 'Financial Analytics'),
    ('Natural Language Processing', 'Information Retrieval'),

    # Materials + Computing
    ('Machine Learning', 'Materials Science'),
    ('Deep Learning', 'Materials Science'),
    ('Machine Learning', 'Nanotechnology'),

    # New domain combinations
    ('Deep Learning', 'Generative AI'),
    ('Quantum Computing', 'Machine Learning'),
    ('Computer Vision', 'Autonomous Systems'),
    ('Machine Learning', 'Structural Engineering'),
    ('Deep Learning', 'Computational Fluid Dynamics'),
    ('Machine Learning', 'Food Science & Technology'),
    ('Natural Language Processing', 'Social Media Analytics'),
    ('Deep Learning', 'Biomedical Sensors'),
    ('Machine Learning', 'VLSI Design'),
    ('Cloud Computing', 'Internet of Things'),
]

# Top 10 most relevant interdisciplinary combinations for quick access
POPULAR_THEME_COMBINATIONS: List[Dict] = [
    {'name': 'AI for Medical Imaging', 'themes': ('Deep Learning', 'Medical Imaging'), 'icon': '🔬'},
    {'name': 'ML for Healthcare', 'themes': ('Machine Learning', 'Healthcare Analytics'), 'icon': '⚕️'},
    {'name': 'IoT + Edge AI', 'themes': ('Internet of Things', 'Edge Computing'), 'icon': '📡'},
    {'name': 'AI Cybersecurity', 'themes': ('Machine Learning', 'Cybersecurity'), 'icon': '🔒'},
    {'name': 'Smart Energy Systems', 'themes': ('Machine Learning', 'Renewable Energy'), 'icon': '⚡'},
    {'name': 'Vision Robotics', 'themes': ('Computer Vision', 'Robotics & Automation'), 'icon': '🤖'},
    {'name': 'Biomedical NLP', 'themes': ('Natural Language Processing', 'Healthcare Analytics'), 'icon': '📋'},
    {'name': 'AI Drug Discovery', 'themes': ('Deep Learning', 'Drug Discovery'), 'icon': '💊'},
    {'name': 'Blockchain Security', 'themes': ('Blockchain & Distributed Ledger', 'Cybersecurity'), 'icon': '⛓️'},
    {'name': 'Smart Manufacturing', 'themes': ('Machine Learning', 'Robotics & Automation'), 'icon': '🏭'},
    {'name': 'Quantum ML', 'themes': ('Quantum Computing', 'Machine Learning'), 'icon': '🔮'},
    {'name': 'Autonomous Drones', 'themes': ('Computer Vision', 'Autonomous Systems'), 'icon': '🛸'},
    {'name': 'GenAI + NLP', 'themes': ('Generative AI', 'Natural Language Processing'), 'icon': '🧠'},
    {'name': 'Smart Structures', 'themes': ('Machine Learning', 'Structural Engineering'), 'icon': '🏗️'},
    {'name': 'Cloud IoT', 'themes': ('Cloud Computing', 'Internet of Things'), 'icon': '☁️'},
]

# =============================================================================
# JOURNAL QUARTILE DATA (Approximate mappings for common journals)
# =============================================================================
JOURNAL_QUARTILES: Dict[str, str] = {
    "nature": "Q1",
    "science": "Q1",
    "ieee transactions": "Q1",
    "elsevier": "Q1-Q2",
    "springer": "Q1-Q2",
    "wiley": "Q1-Q2",
    "taylor & francis": "Q2",
    "mdpi": "Q2-Q3",
    "hindawi": "Q3",
}

# =============================================================================
# CITATION BINS FOR ANALYTICS
# =============================================================================
CITATION_BINS: List[tuple] = [(0, 10), (10, 50), (50, 100), (100, 500), (500, float('inf'))]
CITATION_BIN_LABELS: List[str] = ['0-10', '10-50', '50-100', '100-500', '500+']

# =============================================================================
# UI COLORS
# =============================================================================
UI_COLORS: Dict[str, str] = {
    "primary": "#1E3A8A",
    "secondary": "#3B82F6",
    "success": "#10B981",
    "warning": "#F59E0B",
    "danger": "#EF4444",
    "info": "#06B6D4",
    "light": "#F1F5F9",
    "dark": "#1E293B",
}
