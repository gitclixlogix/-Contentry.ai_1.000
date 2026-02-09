# Global Cultural Sensitivity Analysis Documentation

## Overview

Contentry.ai uses **Hofstede's 6 Cultural Dimensions Framework** to analyze content for global cultural sensitivity. This scientifically-validated framework helps ensure your content resonates appropriately with audiences across different cultural backgrounds.

## Framework: Hofstede's Cultural Dimensions Theory

Developed by Dutch social psychologist **Geert Hofstede** through extensive research at IBM spanning 70+ countries, this framework identifies six key dimensions along which cultural values can be analyzed. It is the most widely used framework for cross-cultural analysis in international business and communication.

---

## The Six Cultural Dimensions

### 1. Power Distance Index (PDI)

**Definition**: The degree to which less powerful members of a society accept and expect that power is distributed unequally.

| High Power Distance | Low Power Distance |
|---------------------|-------------------|
| Formal language, titles | Casual, first-name basis |
| Respect for hierarchy | Egalitarian approach |
| Top-down communication | Open dialogue |
| **Cultures**: Asia, Arab countries, Latin America, Russia | **Cultures**: Nordic countries, Anglo-Saxon, Israel |

**Content Analysis**:
- Does the content use appropriate formality for the target audience?
- Are authority figures referenced respectfully (or too casually)?
- Does the tone match hierarchical expectations?

**Example Issues**:
- Using casual language in content targeting Japanese executives
- Being overly formal in content for Scandinavian startup culture

---

### 2. Individualism vs. Collectivism (IDV)

**Definition**: The degree to which individuals are integrated into groups.

| Individualist Cultures | Collectivist Cultures |
|-----------------------|----------------------|
| "I", "me", "my achievement" | "We", "us", "our community" |
| Personal success stories | Group accomplishments |
| Independence valued | Harmony and loyalty valued |
| **Cultures**: US, UK, Australia, Netherlands | **Cultures**: China, Japan, Korea, Latin America, Africa |

**Content Analysis**:
- Does the content use "I/me" language or "we/us" language?
- Are individual achievements or group benefits highlighted?
- Does the message appeal to personal gain or collective welfare?

**Example Issues**:
- Promoting "personal achievement" to collectivist Asian audiences
- Using "team success" language for highly individualist US entrepreneurs

---

### 3. Masculinity vs. Femininity (MAS)

**Definition**: The distribution of emotional roles between genders - competitive/assertive vs. caring/cooperative values.

| Masculine Cultures | Feminine Cultures |
|-------------------|------------------|
| Competitive language | Cooperative language |
| Achievement, success, winning | Quality of life, consensus |
| Assertive, ambitious | Nurturing, modest |
| **Cultures**: Japan, US, Germany, Italy | **Cultures**: Sweden, Norway, Denmark, Netherlands |

**Content Analysis**:
- Is the content competitive ("be the best") or cooperative ("work together")?
- Does it emphasize winning/success or well-being/balance?
- Is the tone assertive or consensus-seeking?

**Example Issues**:
- Aggressive "crush the competition" messaging for Scandinavian audiences
- Overly soft messaging for competitive Japanese business culture

---

### 4. Uncertainty Avoidance Index (UAI)

**Definition**: A society's tolerance for ambiguity and uncertainty.

| High Uncertainty Avoidance | Low Uncertainty Avoidance |
|---------------------------|--------------------------|
| Clear rules and structure | Flexibility, innovation |
| Detailed explanations | Brief, open-ended content |
| Risk-averse messaging | Embrace of risk/change |
| **Cultures**: Japan, Greece, Portugal, Belgium | **Cultures**: Singapore, Denmark, Sweden, UK |

**Content Analysis**:
- Does the content provide clear, structured information?
- Are claims well-supported with evidence and sources?
- Does it address potential risks and mitigation?

**Example Issues**:
- Vague, ambiguous content for detail-oriented Japanese readers
- Over-explained, rigid content for innovation-friendly Singaporean audience

---

### 5. Long-Term vs. Short-Term Orientation (LTO)

**Definition**: Focus on future rewards vs. short-term results and tradition.

| Long-Term Orientation | Short-Term Orientation |
|----------------------|----------------------|
| Future planning, persistence | Quick results, immediate ROI |
| Adaptation, pragmatism | Tradition, proven methods |
| Thrift, investment | Spending, quick wins |
| **Cultures**: China, Japan, Korea, Germany | **Cultures**: US, UK, Australia, Arab countries |

**Content Analysis**:
- Does the content emphasize long-term benefits or quick wins?
- Is it future-focused or tradition-respecting?
- Does it appeal to patience/investment or immediate gratification?

**Example Issues**:
- "Get rich quick" messaging for long-term oriented Chinese investors
- "5-year strategic vision" content for short-term focused US audience

---

### 6. Indulgence vs. Restraint (IVR)

**Definition**: The extent to which people try to control desires and impulses.

| Indulgent Cultures | Restrained Cultures |
|-------------------|-------------------|
| Fun, enjoyment, optimism | Duty, social norms |
| Happiness emphasized | Gratification controlled |
| Leisure valued | Work ethic emphasized |
| **Cultures**: Latin America, US, UK, Australia | **Cultures**: Eastern Europe, Russia, China, India |

**Content Analysis**:
- Is the tone optimistic and fun, or serious and duty-focused?
- Does it promise enjoyment or emphasize responsibility?
- Are emotions expressed freely or controlled?

**Example Issues**:
- Overly playful content for restrained Eastern European business audience
- Overly serious content for fun-loving Latin American consumers

---

## How Scoring Works

### Dimension-Level Scoring (0-100)

Each dimension is scored based on how well the content aligns with the target audience's cultural expectations:

| Score Range | Meaning |
|-------------|---------|
| **85-100** | Excellent - Content is highly appropriate for this dimension |
| **70-84** | Good - Content aligns well with minor adjustments suggested |
| **50-69** | Moderate - Content may resonate but has cultural risks |
| **30-49** | Poor - Content likely to cause misunderstanding or offense |
| **0-29** | Critical - Content is culturally inappropriate |

### Overall Cultural Score

The **Overall Cultural Score** is calculated as the **weighted average** of all six dimension scores:

```
Overall Score = (PDI + IDV + MAS + UAI + LTO + IVR) / 6
```

### Target Matching

When a **Strategic Profile** has a defined target region/audience, the analysis also provides:

- **Target Match Status**: `good` | `caution` | `poor`
- **Target Match Explanation**: Why the content does/doesn't align with the specific target market

---

## Analysis Output Structure

```json
{
  "cultural_analysis": {
    "overall_score": 75,
    "summary": "Content has strong appeal for Western audiences but may need adjustments for Asian markets.",
    "appropriate_cultures": ["US", "UK", "Australia", "Western Europe"],
    "risk_regions": ["Japan", "China", "Middle East"],
    "target_match_status": "good",
    "target_match_explanation": "Content aligns well with the specified North American target audience.",
    "dimensions": [
      {
        "dimension": "Power Distance",
        "score": 80,
        "feedback": "Content uses appropriately professional but approachable tone.",
        "appropriate_for": ["US", "UK", "Australia", "Scandinavia"],
        "risk_regions": ["Japan", "Korea", "Arab countries"],
        "recommendations": "Consider adding more formal titles when adapting for Asian markets."
      },
      // ... other 5 dimensions
    ]
  }
}
```

---

## Integration with Strategic Profiles

When you select a **Strategic Profile** with defined:
- **Primary Target Region** (e.g., "North America", "Asia-Pacific")
- **Target Audience** (e.g., "B2B Tech Executives", "Young Consumers")

The cultural analysis will:

1. **Evaluate content against the target's cultural expectations**
2. **Highlight alignment or misalignment** with the target market
3. **Provide specific recommendations** for adaptation

---

## Best Practices

### For Global Content

1. **Avoid culture-specific idioms** that don't translate
2. **Use neutral, professional tone** when audience is unknown
3. **Provide context** for culturally-specific references
4. **Balance I/We language** to appeal broadly

### For Targeted Content

1. **Research your target culture's values** using Hofstede Insights
2. **Adjust formality level** based on Power Distance
3. **Frame benefits appropriately** (individual vs. group)
4. **Match emotional tone** to Indulgence/Restraint expectations

---

## References

1. Hofstede, G. (2001). *Culture's Consequences: Comparing Values, Behaviors, Institutions and Organizations Across Nations*. Sage Publications.

2. Hofstede Insights - Country Comparison Tool: https://www.hofstede-insights.com/country-comparison/

3. The Culture Map by Erin Meyer (2014) - Practical applications of cultural dimensions in business communication.

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | Dec 2024 | Initial documentation |
| 1.1 | Jan 2025 | Added appropriate_cultures and target matching |
