import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from backend.models.model_service import model_service
from backend.services.pdf_exporter import pdf_exporter
from backend.services.evidence_verifier import evidence_verifier

def run_tests():
    print("=== TEST 1: Model Service Analysis with Fake News ===")
    fake_headline = "SHOCKING: Secret Government Documents Leaked Proving All Cancer Cures Were Suppressed for Decades!"
    fake_body = "A heroic whistleblower has just LEAKED explosive classified files that the deep state pharmaceutical mafia NEVER wanted you to see! You won't believe what happens when you drink this everyday kitchen juice! Share this VIRAL warning before it gets banned! Wake up sheeple!"
    
    result = model_service.analyze(headline=fake_headline, content=fake_body)
    print(f"Verdict: {result['verdict']}")
    print(f"Model Confidence: {result['model_confidence']}%")
    print(f"Risk Score: {result['misinformation_risk_score']}/100")
    print(f"XAI Top Features: {[f['term'] for f in result['xai_explanation']['top_features'][:4]]}")
    assert result["verdict"] == "LIKELY MISLEADING" or result["misinformation_risk_score"] > 60
    assert len(result["highlighted_analysis"]["spans"]) > 0

    print("\n=== TEST 2: Model Service Analysis with Real News ===")
    real_headline = "Federal Reserve Holds Interest Rates Steady Amid Cooling Inflation Indicators"
    real_body = "The Federal Reserve concluded its two-day Federal Open Market Committee meeting on Wednesday, voting unanimously to maintain the benchmark federal funds rate. In the post-meeting statement, Fed officials cited easing consumer price index data. Economists surveyed by Reuters noted core inflation dropped."
    
    result_real = model_service.analyze(headline=real_headline, content=real_body)
    print(f"Verdict: {result_real['verdict']}")
    print(f"Model Confidence: {result_real['model_confidence']}%")
    print(f"Risk Score: {result_real['misinformation_risk_score']}/100")
    assert result_real["verdict"] == "REAL / LOW RISK" or result_real["misinformation_risk_score"] < 40

    print("\n=== TEST 3: Multi-Model Comparison Check ===")
    for model_k, m_data in result["multi_model_comparison"].items():
        print(f"Model {model_k}: {m_data['prediction']} (Conf: {m_data['confidence']}%, F1: {m_data['f1_score']})")

    print("\n=== TEST 4: PDF Exporter Generation ===")
    pdf_bytes = pdf_exporter.generate_pdf_bytes(result)
    print(f"Generated PDF bytes: {len(pdf_bytes)} bytes")
    assert len(pdf_bytes) > 1000

    print("\n=== TEST 5: Groq Evidence Verifier Check ===")
    evidence = evidence_verifier.verify_claims(fake_headline, fake_body)
    print(f"Evidence Verdict: {evidence.get('overall_evidence_verdict')}")
    print(f"Claims Extracted: {len(evidence.get('claims', []))}")
    print(f"Engine: {evidence.get('engine')}")

    print("\n>>> ALL 5 BACKEND TESTS PASSED SUCCESSFULLY! <<<")

if __name__ == "__main__":
    run_tests()
