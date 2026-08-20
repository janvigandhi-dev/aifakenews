import io
from typing import Dict, Any
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable

class PDFExporter:
    def __init__(self):
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()

    def _setup_custom_styles(self):
        self.title_style = ParagraphStyle(
            'ReportTitle',
            parent=self.styles['Heading1'],
            fontName='Helvetica-Bold',
            fontSize=20,
            leading=24,
            textColor=colors.HexColor('#1E293B'),
            spaceAfter=6
        )
        self.subtitle_style = ParagraphStyle(
            'ReportSubtitle',
            parent=self.styles['Normal'],
            fontName='Helvetica',
            fontSize=10,
            textColor=colors.HexColor('#64748B'),
            spaceAfter=14
        )
        self.section_style = ParagraphStyle(
            'SectionHeader',
            parent=self.styles['Heading2'],
            fontName='Helvetica-Bold',
            fontSize=13,
            leading=16,
            textColor=colors.HexColor('#0F172A'),
            spaceBefore=10,
            spaceAfter=6
        )
        self.body_style = ParagraphStyle(
            'ReportBody',
            parent=self.styles['Normal'],
            fontName='Helvetica',
            fontSize=9,
            leading=13,
            textColor=colors.HexColor('#334155')
        )
        self.bold_body_style = ParagraphStyle(
            'BoldReportBody',
            parent=self.styles['Normal'],
            fontName='Helvetica-Bold',
            fontSize=9,
            leading=13,
            textColor=colors.HexColor('#0F172A')
        )
        self.bullet_style = ParagraphStyle(
            'BulletBody',
            parent=self.styles['Normal'],
            fontName='Helvetica',
            fontSize=9,
            leading=12,
            leftIndent=12,
            textColor=colors.HexColor('#334155'),
            spaceAfter=3
        )
        self.disclaimer_style = ParagraphStyle(
            'DisclaimerText',
            parent=self.styles['Normal'],
            fontName='Helvetica-Oblique',
            fontSize=8,
            leading=11,
            textColor=colors.HexColor('#64748B')
        )

    def generate_pdf_bytes(self, analysis: Dict[str, Any]) -> bytes:
        """Generates a polished TruthLens Fact-Check Analysis PDF report."""
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=letter,
            rightMargin=36,
            leftMargin=36,
            topMargin=36,
            bottomMargin=36
        )

        elements = []

        # 1. Header Banner
        elements.append(Paragraph("TruthLens — Misinformation Assessment Report", self.title_style))
        elements.append(Paragraph("Explainable AI Fake News Detection Platform • https://truthlens.ai", self.subtitle_style))
        elements.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor('#F59E0B'), spaceBefore=2, spaceAfter=10))

        # 2. Executive Summary Table
        verdict = analysis.get("verdict", "REVIEW")
        confidence = analysis.get("model_confidence", 0.0)
        risk_score = analysis.get("misinformation_risk_score", 0.0)
        model_name = analysis.get("active_model", {}).get("name", "Linear SVM")

        # Set color badge based on verdict
        v_color = colors.HexColor('#10B981')
        if verdict == "LIKELY MISLEADING":
            v_color = colors.HexColor('#EF4444')
        elif verdict == "SUSPICIOUS / REVIEW":
            v_color = colors.HexColor('#F59E0B')

        headline_text = analysis.get("headline") or "News Article Analysis"
        url_text = analysis.get("url") or "Manual Text Submission"

        summary_data = [
            [
                Paragraph("<b>Article Headline / Topic:</b>", self.bold_body_style),
                Paragraph(headline_text[:120], self.body_style)
            ],
            [
                Paragraph("<b>Source / URL:</b>", self.bold_body_style),
                Paragraph(url_text[:100], self.body_style)
            ],
            [
                Paragraph("<b>Classification Verdict:</b>", self.bold_body_style),
                Paragraph(f"<font color='{v_color.hexval()}'><b>{verdict}</b></font>", self.bold_body_style)
            ],
            [
                Paragraph("<b>Model Confidence:</b>", self.bold_body_style),
                Paragraph(f"<b>{confidence}%</b> (Statistical class probability)", self.body_style)
            ],
            [
                Paragraph("<b>Misinformation Risk Score:</b>", self.bold_body_style),
                Paragraph(f"<b>{risk_score} / 100</b> (Composite linguistic & ML risk)", self.body_style)
            ],
            [
                Paragraph("<b>Active AI Classifier:</b>", self.bold_body_style),
                Paragraph(f"{model_name}", self.body_style)
            ]
        ]

        summary_table = Table(summary_data, colWidths=[150, 390])
        summary_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#F8FAFC')),
            ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#E2E8F0')),
            ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#E2E8F0')),
            ('PADDING', (0, 0), (-1, -1), 5),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        elements.append(summary_table)
        elements.append(Spacer(1, 10))

        # 3. Key Model Explanations & Signals
        elements.append(Paragraph("Explainability & Rationale Summary", self.section_style))
        explanation_bullets = analysis.get("explanation_bullets", [])
        if explanation_bullets:
            for bullet in explanation_bullets:
                elements.append(Paragraph(f"• {bullet}", self.bullet_style))
        else:
            elements.append(Paragraph("• No severe linguistic anomalies were detected in the supplied text.", self.bullet_style))

        elements.append(Spacer(1, 8))

        # 4. Linguistic Risk Breakdown Table
        elements.append(Paragraph("Linguistic Risk Indicator Breakdown", self.section_style))
        breakdown = analysis.get("linguistic_risk", {}).get("breakdown", {})
        
        indicator_rows = [
            [
                Paragraph("<b>Indicator</b>", self.bold_body_style),
                Paragraph("<b>Severity</b>", self.bold_body_style),
                Paragraph("<b>Score (0-100)</b>", self.bold_body_style),
                Paragraph("<b>Details / Findings</b>", self.bold_body_style)
            ],
            [
                Paragraph("Sensational Language", self.body_style),
                Paragraph(breakdown.get("sensationalism", {}).get("severity", "LOW"), self.body_style),
                Paragraph(str(breakdown.get("sensationalism", {}).get("score", 0)), self.body_style),
                Paragraph(f"{breakdown.get('sensationalism', {}).get('term_count', 0)} hyperbolic terms detected", self.body_style)
            ],
            [
                Paragraph("Clickbait Patterns", self.body_style),
                Paragraph(breakdown.get("clickbait", {}).get("severity", "LOW"), self.body_style),
                Paragraph(str(breakdown.get("clickbait", {}).get("score", 0)), self.body_style),
                Paragraph(f"{breakdown.get('clickbait', {}).get('pattern_count', 0)} curiosity-gap hooks found", self.body_style)
            ],
            [
                Paragraph("Emotional Intensity", self.body_style),
                Paragraph(breakdown.get("emotional_intensity", {}).get("severity", "LOW"), self.body_style),
                Paragraph(str(breakdown.get("emotional_intensity", {}).get("score", 0)), self.body_style),
                Paragraph(f"Subjectivity: {breakdown.get('emotional_intensity', {}).get('subjectivity', 0.0)}", self.body_style)
            ],
            [
                Paragraph("Punctuation & Caps", self.body_style),
                Paragraph(breakdown.get("punctuation_caps", {}).get("severity", "LOW"), self.body_style),
                Paragraph(str(breakdown.get("punctuation_caps", {}).get("score", 0)), self.body_style),
                Paragraph(f"{breakdown.get('punctuation_caps', {}).get('caps_word_count', 0)} uppercase shout words", self.body_style)
            ]
        ]

        ind_table = Table(indicator_rows, colWidths=[140, 70, 90, 240])
        ind_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#F1F5F9')),
            ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#CBD5E1')),
            ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#E2E8F0')),
            ('PADDING', (0, 0), (-1, -1), 4),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        elements.append(ind_table)
        elements.append(Spacer(1, 8))

        # 5. Evidence Verification & Atomic Claims
        evidence = analysis.get("evidence", {})
        if evidence and evidence.get("claims"):
            elements.append(Paragraph("Evidence Verification & Claim Analysis", self.section_style))
            for c in evidence.get("claims", [])[:3]:
                stance = c.get("stance", "UNVERIFIED")
                s_color = "#10B981" if stance == "SUPPORTED" else ("#EF4444" if stance == "CONTRADICTED" else "#F59E0B")
                elements.append(Paragraph(f"<b>Claim:</b> \"{c.get('claim', '')}\"", self.bold_body_style))
                elements.append(Paragraph(f"<b>Stance:</b> <font color='{s_color}'><b>{stance}</b></font> — {c.get('evidence_assessment', '')}", self.body_style))
                elements.append(Spacer(1, 3))
            elements.append(Spacer(1, 6))

        # 6. Multi-Model Comparison
        comparison = analysis.get("multi_model_comparison", {})
        if comparison:
            elements.append(Paragraph("Comparative Multi-Model Classifier Assessment", self.section_style))
            model_rows = [[
                Paragraph("<b>Classifier</b>", self.bold_body_style),
                Paragraph("<b>Architecture</b>", self.bold_body_style),
                Paragraph("<b>Prediction</b>", self.bold_body_style),
                Paragraph("<b>Confidence</b>", self.bold_body_style),
                Paragraph("<b>Benchmark F1</b>", self.bold_body_style)
            ]]
            for key, m in comparison.items():
                p_text = m.get("prediction", "")
                p_color = "#EF4444" if p_text == "MISLEADING" else "#10B981"
                model_rows.append([
                    Paragraph(m.get("model_name", key), self.body_style),
                    Paragraph(m.get("model_type", "ML Model"), self.body_style),
                    Paragraph(f"<font color='{p_color}'><b>{p_text}</b></font>", self.body_style),
                    Paragraph(f"{m.get('confidence', 0)}%", self.body_style),
                    Paragraph(f"{m.get('f1_score', 0):.2f}", self.body_style)
                ])

            comp_table = Table(model_rows, colWidths=[140, 150, 90, 80, 80])
            comp_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#F1F5F9')),
                ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#CBD5E1')),
                ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#E2E8F0')),
                ('PADDING', (0, 0), (-1, -1), 3),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ]))
            elements.append(comp_table)
            elements.append(Spacer(1, 10))

        # 7. Ethical Disclaimer & Limitations (Section 36 & 45 of prompt)
        elements.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor('#CBD5E1'), spaceBefore=6, spaceAfter=6))
        elements.append(Paragraph("<b>Academic Methodology & Limitations Notice:</b>", self.bold_body_style))
        disclaimer_text = (
            "TruthLens is an explainable AI research and screening tool. Statistical model confidence represents pattern alignment "
            "with learned historical training data, NOT absolute factual truth. False positives, false negatives, concept drift, and "
            "dataset domain shifts may occur. Users should always corroborate critical news with primary authoritative sources and accredited fact-checkers."
        )
        elements.append(Paragraph(disclaimer_text, self.disclaimer_style))

        # Build PDF
        doc.build(elements)
        buffer.seek(0)
        return buffer.getvalue()

pdf_exporter = PDFExporter()
