"""
SASTRA Research Finder - Theme Service
Manages research domains and themes - both static and dynamic.
"""

from typing import List, Dict, Optional, Any
from sqlalchemy.orm import Session

from app.core.config import get_settings, THEMATIC_AREAS
from app.models.db_models import ResearchDomain, ResearchTheme


DOMAIN_MAPPING = {
    # Core AI & Machine Learning
    'Machine Learning': 'Artificial Intelligence',
    'Deep Learning': 'Artificial Intelligence',
    'Reinforcement Learning': 'Artificial Intelligence',
    'Transfer Learning': 'Artificial Intelligence',
    'Explainable AI': 'Artificial Intelligence',
    'Federated Learning': 'Artificial Intelligence',
    'Computer Vision': 'Artificial Intelligence',
    'Natural Language Processing': 'Artificial Intelligence',
    'Generative AI': 'Artificial Intelligence',
    'Ethical AI & AI Governance': 'Artificial Intelligence',
    
    # Data Science
    'Data Science & Analytics': 'Data Science',
    'Time Series Analysis': 'Data Science',
    'Recommender Systems': 'Data Science',
    'Graph Analytics': 'Data Science',
    'Information Retrieval': 'Data Science',
    
    # Healthcare
    'Medical Imaging': 'Healthcare & Biomedical',
    'Healthcare Analytics': 'Healthcare & Biomedical',
    'Drug Discovery': 'Healthcare & Biomedical',
    'Bioinformatics': 'Healthcare & Biomedical',
    'Wearable Health Technology': 'Healthcare & Biomedical',
    'Mental Health AI': 'Healthcare & Biomedical',
    'Biomedical Sensors': 'Healthcare & Biomedical',
    'Tissue Engineering': 'Healthcare & Biomedical',
    'Prosthetics & Rehabilitation': 'Healthcare & Biomedical',
    
    # Security
    'Cybersecurity': 'Cybersecurity & Privacy',
    'Privacy & Data Protection': 'Cybersecurity & Privacy',
    'Blockchain & Distributed Ledger': 'Cybersecurity & Privacy',
    'Network Security': 'Cybersecurity & Privacy',
    
    # IoT & Wireless
    'Internet of Things': 'IoT & Embedded Systems',
    'Edge Computing': 'IoT & Embedded Systems',
    'Smart Agriculture': 'IoT & Embedded Systems',
    'Wireless Communication': 'IoT & Embedded Systems',
    'Embedded Systems': 'IoT & Embedded Systems',
    'FPGA & Reconfigurable Computing': 'IoT & Embedded Systems',
    'VLSI Design': 'IoT & Embedded Systems',
    
    # Energy
    'Renewable Energy': 'Energy & Power',
    'Power Systems': 'Energy & Power',
    'Energy Storage': 'Energy & Power',
    'Environmental Engineering': 'Energy & Power',
    'Electric Vehicles': 'Energy & Power',
    
    # Materials
    'Materials Science': 'Materials & Manufacturing',
    'Nanotechnology': 'Materials & Manufacturing',
    'Additive Manufacturing': 'Materials & Manufacturing',
    'Robotics & Automation': 'Materials & Manufacturing',
    'Control Systems': 'Materials & Manufacturing',
    
    # Signal Processing
    'Signal Processing': 'Signal & Image Processing',
    'Speech & Audio Processing': 'Signal & Image Processing',
    'Image & Video Processing': 'Signal & Image Processing',
    'Radar & Remote Sensing': 'Signal & Image Processing',
    
    # Optimization
    'Optimization Algorithms': 'Optimization & Operations',
    'Operations Research': 'Optimization & Operations',
    'Financial Analytics': 'Optimization & Operations',
    'Digital Twin': 'Optimization & Operations',
    
    # Computing
    'Cloud Computing': 'Computing & Infrastructure',
    'Distributed Systems': 'Computing & Infrastructure',
    'High-Performance Computing': 'Computing & Infrastructure',
    'Software Engineering': 'Computing & Infrastructure',
    'Software Testing & Quality': 'Computing & Infrastructure',
    'Human-Computer Interaction': 'Computing & Infrastructure',
    
    # Engineering
    'Structural Engineering': 'Civil & Structural Engineering',
    'Geotechnical Engineering': 'Civil & Structural Engineering',
    'Transportation Engineering': 'Civil & Structural Engineering',
    'Water Resources Engineering': 'Civil & Structural Engineering',
    
    # Mathematics
    'Mathematical Modeling': 'Mathematical Sciences',
    'Numerical Methods': 'Mathematical Sciences',
    'Combinatorics & Graph Theory': 'Mathematical Sciences',
    'Stochastic Processes': 'Mathematical Sciences',
    
    # Physics
    'Optical Engineering & Photonics': 'Physics & Photonics',
    'Quantum Computing': 'Physics & Photonics',
    'Semiconductor Devices': 'Physics & Photonics',
    'Condensed Matter Physics': 'Physics & Photonics',
    
    # Chemistry
    'Organic Chemistry': 'Chemistry',
    'Analytical Chemistry': 'Chemistry',
    'Catalysis & Reaction Engineering': 'Chemistry',
    'Chemical Process Engineering': 'Chemistry',
    
    # Education
    'Educational Technology': 'Education & Pedagogy',
    'STEM Education': 'Education & Pedagogy',
    'Natural Language Understanding': 'Education & Pedagogy',
    
    # Management
    'Human Resource Analytics': 'Management & Economics',
    'Marketing Analytics': 'Management & Economics',
    'Entrepreneurship & Innovation': 'Management & Economics',
    
    # Networking
    'Optical Networks': 'Networking & Communications',
    'Ad Hoc & Sensor Networks': 'Networking & Communications',
    'Software-Defined Networking': 'Networking & Communications',
    
    # Thermal
    'Computational Fluid Dynamics': 'Thermal & Fluid Engineering',
    'Heat Transfer Engineering': 'Thermal & Fluid Engineering',
    'Microfluidics': 'Thermal & Fluid Engineering',
    
    # Agriculture
    'Food Science & Technology': 'Agriculture & Food Science',
    'Crop Science & Plant Biology': 'Agriculture & Food Science',
    
    # Social
    'Social Media Analytics': 'Computational Social Science',
    'Computational Social Science': 'Computational Social Science',
    'Legal Informatics': 'Computational Social Science',
    
    # Emerging
    'Augmented & Virtual Reality': 'Emerging Technologies',
    'Autonomous Systems': 'Emerging Technologies',
    
    # Misc
    'Corrosion Science': 'Miscellaneous Engineering',
    'Tribology': 'Miscellaneous Engineering',
    'Acoustics & Vibration': 'Miscellaneous Engineering',
    'Reliability Engineering': 'Miscellaneous Engineering',
}


def get_domain_color(domain_name: str) -> str:
    """Get color for domain"""
    colors = {
        'Artificial Intelligence': '#8B5CF6',
        'Data Science': '#3B82F6',
        'Healthcare & Biomedical': '#10B981',
        'Cybersecurity & Privacy': '#EF4444',
        'IoT & Embedded Systems': '#F59E0B',
        'Energy & Power': '#06B6D4',
        'Materials & Manufacturing': '#EC4899',
        'Signal & Image Processing': '#14B8A6',
        'Optimization & Operations': '#6366F1',
        'Computing & Infrastructure': '#0EA5E9',
        'Civil & Structural Engineering': '#84CC16',
        'Mathematical Sciences': '#F97316',
        'Physics & Photonics': '#A855F7',
        'Chemistry': '#22C55E',
        'Education & Pedagogy': '#EAB308',
        'Management & Economics': '#F43F5E',
        'Networking & Communications': '#06B6D4',
        'Thermal & Fluid Engineering': '#8B5CF6',
        'Agriculture & Food Science': '#22C55E',
        'Computational Social Science': '#6366F1',
        'Emerging Technologies': '#E11D48',
        'Miscellaneous Engineering': '#6B7280',
    }
    return colors.get(domain_name, '#6B7280')


def seed_domains_and_themes(db: Session):
    """Seed domains and themes from config into database."""
    settings = get_settings()
    
    # Track which themes we've seen
    seen_themes = set()
    
    # First, create all domains
    domain_order = 0
    for theme_name in THEMATIC_AREAS.keys():
        domain_name = DOMAIN_MAPPING.get(theme_name, 'Miscellaneous Engineering')
        
        if domain_name not in seen_themes:
            seen_themes.add(domain_name)
            
            # Check if domain exists
            existing_domain = db.query(ResearchDomain).filter(
                ResearchDomain.name == domain_name
            ).first()
            
            if not existing_domain:
                domain = ResearchDomain(
                    name=domain_name,
                    description=f"Research domain for {domain_name}",
                    color=get_domain_color(domain_name),
                    order_index=domain_order,
                    is_dynamic=False
                )
                db.add(domain)
                domain_order += 1
    
    db.commit()
    
    # Now create themes
    for theme_name, keywords in THEMATIC_AREAS.items():
        domain_name = DOMAIN_MAPPING.get(theme_name, 'Miscellaneous Engineering')
        
        # Get domain
        domain = db.query(ResearchDomain).filter(
            ResearchDomain.name == domain_name
        ).first()
        
        if not domain:
            continue
        
        # Check if theme exists
        existing_theme = db.query(ResearchTheme).filter(
            ResearchTheme.name == theme_name
        ).first()
        
        if not existing_theme:
            theme = ResearchTheme(
                domain_id=domain.id,
                name=theme_name,
                keywords=keywords,
                is_dynamic=False,
                source='static'
            )
            db.add(theme)
    
    db.commit()
    print("Seeded domains and themes from config")


def get_all_themes(db: Session, include_dynamic: bool = True) -> List[Dict[str, Any]]:
    """Get all themes grouped by domain."""
    query = db.query(ResearchTheme).filter(ResearchTheme.is_active == True)
    
    themes = query.all()
    
    # Group by domain
    result = {}
    for theme in themes:
        domain_name = theme.domain.name if theme.domain else 'Uncategorized'
        if domain_name not in result:
            result[domain_name] = {
                'id': theme.domain.id if theme.domain else None,
                'name': domain_name,
                'color': theme.domain.color if theme.domain else '#6B7280',
                'themes': []
            }
        result[domain_name]['themes'].append({
            'id': theme.id,
            'name': theme.name,
            'keywords': theme.keywords or [],
            'paper_count': theme.paper_count,
            'faculty_count': theme.faculty_count,
            'is_dynamic': theme.is_dynamic
        })
    
    return list(result.values())


def get_theme_by_name(db: Session, name: str) -> Optional[ResearchTheme]:
    """Get theme by name."""
    return db.query(ResearchTheme).filter(ResearchTheme.name == name).first()


def create_dynamic_theme(
    db: Session,
    name: str,
    domain_name: str,
    keywords: List[str],
    description: str = None
) -> ResearchTheme:
    """Create a new dynamic theme."""
    # Find or create domain
    domain = db.query(ResearchDomain).filter(ResearchDomain.name == domain_name).first()
    
    if not domain:
        domain = ResearchDomain(
            name=domain_name,
            description=f"Dynamic domain: {domain_name}",
            color=get_domain_color(domain_name),
            is_dynamic=True
        )
        db.add(domain)
        db.commit()
        db.refresh(domain)
    
    # Check if theme already exists
    existing = db.query(ResearchTheme).filter(ResearchTheme.name == name).first()
    if existing:
        return existing
    
    # Create new theme
    theme = ResearchTheme(
        domain_id=domain.id,
        name=name,
        keywords=keywords,
        description=description,
        is_dynamic=True,
        source='dynamic'
    )
    db.add(theme)
    db.commit()
    db.refresh(theme)
    
    return theme


def get_themes_for_team_builder(db: Session) -> List[str]:
    """Get list of theme names for team builder."""
    themes = db.query(ResearchTheme).filter(
        ResearchTheme.is_active == True,
        ResearchTheme.faculty_count > 0
    ).all()
    return [t.name for t in themes]