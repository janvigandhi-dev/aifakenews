import csv
import random
from pathlib import Path
import pandas as pd
from backend.config import DATA_DIR

# Rich collection of real and fake articles spanning multiple categories: Politics, Health/Medicine, Science, Technology, World, Climate, Finance.

REAL_NEWS_TEMPLATES = [
    # Politics & Policy
    ("Bipartisan Senate Committee Unveils Comprehensive Infrastructure Investment Proposal",
     "A bipartisan group of senators today introduced a $550 billion infrastructure package focused on modernizing transportation corridors, public transit networks, and municipal water management systems. According to committee members, the legislation seeks to allocate funding over a five-year timeline, with disbursements overseen by federal oversight bodies. The Congressional Budget Office stated that an independent economic review is underway to evaluate long-term debt impacts. Representative Miller noted during the press briefing that negotiations remain ongoing regarding specific funding mechanisms, and formal committee votes are scheduled for next Tuesday.",
     "politics"),
    
    ("Federal Reserve Holds Interest Rates Steady Amid Cooling Inflation Indicators",
     "The Federal Reserve concluded its two-day Federal Open Market Committee meeting on Wednesday, voting unanimously to maintain the benchmark federal funds rate. In the post-meeting statement, Fed officials cited easing consumer price index data and stable labor market conditions as justification for holding policy steady. Economists surveyed by Reuters noted that core inflation dropped 0.2 percentage points over the past quarter, reflecting tighter credit conditions. Fed Chairman Powell emphasized during the news conference that upcoming policy decisions will remain strictly data-dependent.",
     "finance"),
     
    ("World Health Organization Releases Updated Global Vaccination and Surveillance Guidelines",
     "The World Health Organization today published its updated strategic framework for respiratory pathogen surveillance and seasonal vaccination protocols. The comprehensive report, compiled by an international panel of infectious disease epidemiologists, outlines testing standards for member states. Dr. Tedros Adhanom Ghebreyesus stated in Geneva that sustained genomic monitoring is crucial for early detection of viral variants. Clinical trials cited in the bulletin demonstrated vaccine efficacy rates exceeding 88% in reducing severe hospitalizations across surveyed regions.",
     "health"),

    ("NASA James Webb Space Telescope Identifies Atmospheric Water Vapor in Exoplanet Orbit",
     "Astrophysicists analyzing spectroscopic data from the James Webb Space Telescope have confirmed the presence of atmospheric water vapor on exoplanet WASP-96b, located approximately 1,150 light-years away. The peer-reviewed study, published in the journal Nature Astronomy, utilized near-infrared instruments to measure chemical absorption signatures during planetary transit. Lead researcher Dr. Elena Vance explained that while the high atmospheric temperatures make the planet uninhabitable, the precision measurements provide critical insights into planetary formation models.",
     "science"),

    ("European Union Passes Landmark AI Regulatory Framework with Strict Risk Tiers",
     "European lawmakers officially approved the European Union Artificial Intelligence Act following months of inter-institutional negotiations in Brussels. The legislation establishes a risk-tiered compliance framework, prohibiting high-risk biometric mass surveillance while enforcing transparency standards for general-purpose foundation models. According to the European Commission's press release, companies developing enterprise AI systems will have an 18-month grace period to implement compliance audits and data governance reporting.",
     "technology"),

    ("United Nations Climate Summit Concludes with Historic Renewable Energy Target Agreement",
     "Delegates representing 195 member nations concluded the UN Climate Conference today, signing a binding declaration to triple global renewable energy generation capacity by 2030. The final agreement, ratified after extensive late-night negotiations, establishes a dedicated loss-and-damage transition fund for developing island states. Independent climate policy analysts from the International Energy Agency noted that achieving the targets will require an estimated $4.5 trillion in annual clean energy investments.",
     "climate"),

    ("Supreme Court Hears Oral Arguments on Digital Privacy and Warrantless Geolocation Tracking",
     "The Supreme Court heard oral arguments Tuesday in a pivotal Fourth Amendment dispute concerning whether law enforcement agencies may purchase commercial geolocation data from data brokers without a search warrant. Justices questioned attorneys representing both the Department of Justice and civil liberties organizations regarding the boundary between voluntary commercial disclosure and reasonable expectations of privacy in the digital age. A written decision is expected before the court's summer recess.",
     "politics"),

    ("International Energy Agency Reports 25% Increase in Global Solar Grid Deployments",
     "Global solar photovoltaic capacity expanded by 25% over the previous fiscal year, according to the annual market review released by the International Energy Agency. Falling manufacturing costs for polysilicon cells and expanded tax credits in North America and East Asia drove record adoption rates. The report highlights that solar installations outpaced all other power generation sources combined for the third consecutive year.",
     "finance"),

    ("Clinical Trial Confirms Efficacy of Targeted Antibody Treatment for Early-Stage Alzheimer's",
     "Results from a Phase 3 randomized, double-blind clinical trial published in the New England Journal of Medicine indicate that a monoclonal antibody treatment slowed cognitive decline by 27% in patients diagnosed with early-stage Alzheimer's disease. The trial, conducted across 140 medical centers with 1,800 participants over an 18-month period, monitored amyloid plaque reduction via PET scans. Neurologists cautioned that while the drug does not restore lost cognitive function, it marks a significant clinical milestone.",
     "health"),

    ("Department of Transportation Announces $1.2B Grant for High-Speed Rail Modernization",
     "The U.S. Department of Transportation announced $1.2 billion in federal infrastructure grants aimed at upgrading passenger rail corridors in the Pacific Northwest and Midwest. Transportation Secretary Pete Buttigieg confirmed that the funding will eliminate at-grade crossings, electrify 150 miles of track, and procure energy-efficient trainsets. Regional transit authorities reported that construction contracts will open for competitive bidding next month.",
     "politics")
]

FAKE_NEWS_TEMPLATES = [
    # Clickbait & Conspiracies
    ("SHOCKING: Secret Government Documents Leaked Proving All Cancer Cures Were Suppressed for Decades!",
     "A heroic whistleblower has just LEAKED explosive classified files that the deep state pharmaceutical mafia NEVER wanted you to see! The mind-blowing documents confirm that a 100% natural herbal remedy discovered in 1952 cures all forms of terminal cancer in just 48 hours, but corrupt billionaire elites buried it to protect their multi-trillion dollar profits! Mainstream media is under complete blackout! You won't believe what happens when you drink this everyday kitchen juice! Share this VIRAL warning before it gets banned and deleted from the internet forever! Wake up sheeple!",
     "health"),

    ("YOU WON'T BELIEVE THIS: Scientists Reveal One Bizarre Trick That Instantly Eliminates All Debt!",
     "Banks and Wall Street millionaires are FURIOUS after an anonymous rogue mathematician exposed this one simple secret loop-hole that completely wipes out your mortgage, credit cards, and student loans overnight! Federal authorities are scrambling to shut down this webpage immediately! Doctors and financial advisors hate him for exposing the hidden truth! Click here right now to see the shocking video before corrupt bankers take it down!",
     "finance"),

    ("BREAKING BOMBSHELL: UN Caught Spraying Mind-Control Chemicals From Commercial Airplanes!",
     "Emergency alert for all citizens! Shocking indisputable proof has emerged confirming that globalist elites at the United Nations have been secretly spraying toxic mind-control aerosols in our atmosphere! Pilot whistleblowers have finally broken their silence, exposing secret government valves hidden inside jet turbines. The corrupt mainstream media is completely silent on this monstrous treason! If you look up in the sky, you will see the terrifying truth! Spread this urgent red alert everywhere!",
     "conspiracy"),

    ("THIS CHANGES EVERYTHING: Ancient 5,000-Year-Old Alien City Discovered Beneath Antarctica Ice!",
     "An elite team of underground researchers made a jaw-dropping discovery that will shatter human history! High-resolution thermal satellites have exposed massive pyramid structures and advanced alien technology buried deep beneath the Antarctic ice sheet. Pentagon officials are reportedly in total panic and attempting a media blackout to keep humanity in the dark! What they found inside will blow your mind! See the shocking photos they don't want you to see!",
     "science"),

    ("MIRACLE BREAKTHROUGH: Drink This One Common Spice and Burn 40 Pounds of Pure Fat While You Sleep!",
     "Fitness gurus and diet pill companies are TERRIFIED of this miraculous new discovery! Top researchers at an underground institute have proven once and for all that a single spoon of this exotic secret spice melts away belly fat without diet or exercise! Over 500,000 people have already used this unbelievable hack. Big Pharma is trying to ban this product tomorrow! Claim your secret bottle before it's gone forever!",
     "health"),

    ("EXPOSED: Secret Bill Passed at Midnight to Confiscate All Personal Bank Accounts Next Week!",
     "Red alert! In a secret midnight vote behind closed doors, corrupt politicians passed an unconstitutional decree allowing the government to seize your private savings and retirement funds! Insiders warn that a total banking collapse is engineered for next Friday! The puppet media is refusing to cover this catastrophic scandal! You must withdraw all cash immediately before the banks lock their doors forever!",
     "politics"),

    ("SHOCKING TRUTH: 5G Towers Are Secretly Transmitting Frequencies That Control Human Emotions!",
     "A top classified military manual leaked online reveals that new wireless cell towers are not for communication, but are actually weaponized psychological frequency emitters designed to keep the population docile and obedient! Leaked blueprints prove that globalist engineers designed the hardware to trigger mass panic and obedience on demand. Read the explosive truth before this post is censored!",
     "technology"),

    ("YOU MUST SEE THIS: Secret Celebrity Scandal Shuts Down Live Broadcast as Security Storms Stage!",
     "Chaos erupted during a live television broadcast yesterday when a beloved celebrity accidentally blurted out the shocking secret method they used to generate millions in automated income! The network cut the feed immediately and security escorted them off stage, but an audience member recorded the entire incident! See the unbelievable transcript before their high-powered lawyers scrub it from the web!",
     "clickbait"),

    ("DISASTER ALERT: Meteor Twice the Size of Mount Everest on Direct Collision Course With Earth Next Month!",
     "World governments have secretly prepared luxury underground bunkers while leaving the rest of the world completely unprepared! Astronomical whistleblowers confirm an apocalyptic asteroid is hurtling toward Earth at 60,000 miles per hour! NASA is hiding the terrifying data to prevent global riots! Share this urgent message to warn your loved ones before it's too late!",
     "science"),

    ("PROOF: Government Has Been Secretly Cloning World Leaders in Underground Mountain Bunkers!",
     "Leaked security footage from a top-secret subterranean facility reveals rows of genetic cloning pods containing biological duplicates of prominent political figures! The corrupt deep state has reportedly replaced key officials with synthetic obedient clones to execute their sinister global agenda! The mainstream fake news won't dare mention this explosive investigation! Wake up and share!",
     "conspiracy")
]

# Variations and synthetic expansions to build a balanced dataset of 1,200+ samples
def generate_dataset_records(num_samples: int = 1400) -> pd.DataFrame:
    """Generates a rich, balanced training and validation dataset with realistic variations."""
    records = []
    
    # Real news expansion templates with variations
    real_subjects = [
        "Treasury Department", "World Bank", "Center for Disease Control", "European Space Agency",
        "Department of Energy", "International Monetary Fund", "National Science Foundation",
        "Environmental Protection Agency", "Federal Communications Commission", "Securities and Exchange Commission"
    ]
    
    real_actions = [
        "releases quarterly economic performance audit indicating steady regional growth",
        "announces $450 million research grant for clean water infrastructure modernization",
        "publishes peer-reviewed findings on renewable battery storage efficiency",
        "concludes multilateral trade dialogue with verified regulatory harmonization",
        "initiates nationwide clinical monitoring program for early respiratory screening",
        "reports 14% reduction in industrial carbon emissions across manufacturing sectors",
        "approves new diagnostic testing protocols following extensive multicenter trials",
        "issues comprehensive guidance on semiconductor manufacturing supply chains"
    ]

    real_quotes = [
        "According to official statements, the program will undergo independent audits every six months.",
        "The peer-reviewed study, conducted across twelve research universities, confirmed statistical significance.",
        "Government representatives emphasized that implementation guidelines remain open for public commentary.",
        "Economists and industry analysts noted that the gradual rollout minimizes market volatility.",
        "Data compiled by independent statisticians showed consistent improvements across all survey metrics."
    ]

    # Fake news expansion templates with variations
    fake_subjects = [
        "Deep State Insiders", "Secret Globalist Cabal", "Underground Whistleblowers",
        "Rogue Ex-Military Scientists", "Banned Natural Doctors", "Anonymous Hackers",
        "Classified Military Personnel", "Billionaire Oligarchs"
    ]

    fake_actions = [
        "LEAK SHOCKING PROOF of Secret Plan to Poison Public Drinking Water With Mind-Controlling Nanobots!",
        "EXPOSE Secret Device That Creates Free Endless Energy But Was Banned by Oil Monopolies!",
        "CONFIRM Corrupt Media Is Hiding The Miracle One-Minute Cure For All Deadly Illnesses!",
        "UNMASK Explosive Conspiracy by Global Elites to Ban All Cash and Freeze Citizen Accounts!",
        "REVEAL Terrifying Secret Weather Weapon Causing Earthquakes and Hurricanes On Demand!",
        "WARN That New Satellite Network Transmits Harmful Frequencies Designed To Trigger Total Chaos!"
    ]

    fake_urgencies = [
        "You won't believe what happens next! Share this viral video before government agents delete it!",
        "Doctors are outraged and trying to ban this webpage! Read the shocking truth right now!",
        "Mainstream media is under strict gag orders! Spread this urgent red alert to all your friends!",
        "This one simple secret trick destroys their corrupt system! See the proof before it's too late!",
        "Wake up sheeple! They are lying to you every single day! Don't let them silence the truth!"
    ]

    # 1. Base Real Articles
    for headline, body, category in REAL_NEWS_TEMPLATES:
        records.append({
            "headline": headline,
            "text": body,
            "category": category,
            "label": 0,  # 0 = Real / Credible
            "label_name": "REAL"
        })

    # 2. Base Fake Articles
    for headline, body, category in FAKE_NEWS_TEMPLATES:
        records.append({
            "headline": headline,
            "text": body,
            "category": category,
            "label": 1,  # 1 = Fake / Misinformation
            "label_name": "FAKE"
        })

    # 3. Generate Synthetically Varied Real Articles
    random.seed(42)
    for i in range(num_samples // 2 - len(REAL_NEWS_TEMPLATES)):
        subj = random.choice(real_subjects)
        action = random.choice(real_actions)
        quote1 = random.choice(real_quotes)
        quote2 = random.choice(real_quotes)
        headline = f"{subj} {action.capitalize()}"
        body = (
            f"The {subj} on Tuesday announced that it {action}. "
            f"{quote1} Officials confirmed that the policy was developed following multi-stakeholder consultations. "
            f"{quote2} Representatives from local regulatory bodies stated that full documentation has been submitted "
            f"for formal legislative review. Additional technical briefings are scheduled for next month."
        )
        records.append({
            "headline": headline,
            "text": body,
            "category": "general_news",
            "label": 0,
            "label_name": "REAL"
        })

    # 4. Generate Synthetically Varied Fake Articles
    for i in range(num_samples // 2 - len(FAKE_NEWS_TEMPLATES)):
        subj = random.choice(fake_subjects)
        action = random.choice(fake_actions)
        urgency1 = random.choice(fake_urgencies)
        urgency2 = random.choice(fake_urgencies)
        headline = f"SHOCKING: {subj} {action}"
        body = (
            f"In an UNBELIEVABLE leaked development, {subj} have just {action.lower()}! "
            f"This explosive bombshell proves once and for all what corrupt elites have been hiding for decades! "
            f"{urgency1} Corrupt mainstream media refuses to broadcast this massive scandal. "
            f"{urgency2} Millions of people are waking up to this indisputable proof! Spread the word immediately!"
        )
        records.append({
            "headline": headline,
            "text": body,
            "category": "misinformation",
            "label": 1,
            "label_name": "FAKE"
        })

    random.shuffle(records)
    df = pd.DataFrame(records)
    return df

def save_benchmark_dataset():
    """Generates and persists the benchmark training CSV dataset."""
    df = generate_dataset_records(1400)
    dataset_path = DATA_DIR / "benchmark_dataset.csv"
    df.to_csv(dataset_path, index=False)
    print(f"[DatasetBuilder] Saved {len(df)} records ({sum(df['label'] == 0)} Real, {sum(df['label'] == 1)} Fake) to {dataset_path}")
    return dataset_path

if __name__ == "__main__":
    save_benchmark_dataset()
