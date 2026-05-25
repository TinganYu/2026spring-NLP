# https://chatgpt.com/share/6a134cef-0cd8-83e8-9a7c-89c5450d1b6d
{
    "date": "2026-05-25",
    "emotion_label": "negative",
    "emotion_score": 0.7185929648241206,
    "symptoms": [
        {
            "key": "Muscular stiffness",
            "display": "stiff",
            "status": "affirmed",
            "severity": 1
        },
        {
            "key": "Low Back Pain",
            "display": "lower back pain",
            "status": "affirmed",
            "severity": 3
        },
        {
            "key": "bit - unit of measure",
            "display": "bit",
            "status": "affirmed",
            "severity": 1
        },
        {
            "key": "Down Syndrome",
            "display": "down",
            "status": "affirmed",
            "severity": 1
        },
        {
            "key": "Traumatic injury",
            "display": "injury",
            "status": "affirmed",
            "severity": 1
        },
        {
            "key": "Flare-up",
            "display": "flare up",
            "status": "affirmed",
            "severity": 1
        },
        {
            "key": "Feel Healthy",
            "display": "feel better",
            "status": "hypothetical",
            "severity": 1
        }
    ],
    "medications": [],
    "events": [
        {
            "type": "TimeOfCondition",
            "roles": {
                "Time": "today",
                "Condition": "stiff"
            },
            "text": "stiff 發生在 today"
        },
        {
            "type": "TimeOfCondition",
            "roles": {
                "Time": "today",
                "Condition": "lower back pain"
            },
            "text": "lower back pain 發生在 today"
        },
        {
            "type": "QualifierOfCondition",
            "roles": {
                "Qualifier": "extremely",
                "Condition": "stiff"
            },
            "text": "QualifierOfCondition: Qualifier=extremely, Condition=stiff"
        },
        {
            "type": "BodySiteOfCondition",
            "roles": {
                "Condition": "stiff",
                "BodyStructure": "lower back"
            },
            "text": "BodySiteOfCondition: Condition=stiff, BodyStructure=lower back"
        },
        {
            "type": "QualifierOfCondition",
            "roles": {
                "Qualifier": "moderate",
                "Condition": "lower back pain"
            },
            "text": "QualifierOfCondition: Qualifier=moderate, Condition=lower back pain"
        },
        {
            "type": "QualifierOfCondition",
            "roles": {
                "Qualifier": "severe",
                "Condition": "lower back pain"
            },
            "text": "QualifierOfCondition: Qualifier=severe, Condition=lower back pain"
        },
        {
            "type": "TimeOfCondition",
            "roles": {
                "Condition": "down",
                "Time": "yesterday"
            },
            "text": "down 發生在 yesterday"
        },
        {
            "type": "QualifierOfCondition",
            "roles": {
                "Qualifier": "old",
                "Condition": "injury"
            },
            "text": "QualifierOfCondition: Qualifier=old, Condition=injury"
        },
        {
            "type": "TimeOfCondition",
            "roles": {
                "Condition": "feel better",
                "Time": "afternoon"
            },
            "text": "feel better 發生在 afternoon"
        }
    ]
}









{
    "date": "2026-05-25",
    "emotion_label": "negative",
    "emotion_score": 0.98,
    "symptoms": [
        {
            "key": "Back Pain",
            "display": "back pain",
            "status": "affirmed",
            "severity": 1
        },
        {
            "key": "couldn't sleep well",
            "display": "couldn't sleep well",
            "status": "affirmed",
            "severity": 1
        },
        {
            "key": "tossed",
            "display": "tossed",
            "status": "affirmed",
            "severity": 1
        },
        {
            "key": "Does turn (finding)",
            "display": "turned",
            "status": "affirmed",
            "severity": 1
        },
        {
            "key": "Feeling tired",
            "display": "tired",
            "status": "affirmed",
            "severity": 1
        },
        {
            "key": "Irritable Mood",
            "display": "irritable",
            "status": "affirmed",
            "severity": 1
        },
        {
            "key": "Pain",
            "display": "pain",
            "status": "affirmed",
            "severity": 1
        },
        {
            "key": "Relaxed",
            "display": "relaxed",
            "status": "affirmed",
            "severity": 1
        }
    ],
    "medications": [
        {
            "key": "ibuprofen",
            "display": "ibuprofen",
            "frequency": "",
            "inferred": false
        }
    ],
    "events": [
        {
            "type": "TimeOfCondition",
            "roles": {
                "Time": "Last night",
                "Condition": "back pain"
            },
            "text": "back pain 發生在 Last night"
        },
        {
            "type": "TimeOfCondition",
            "roles": {
                "Condition": "couldn't sleep well",
                "Time": "all night"
            },
            "text": "couldn't sleep well 發生在 all night"
        },
        {
            "type": "TimeOfCondition",
            "roles": {
                "Condition": "tossed",
                "Time": "all night"
            },
            "text": "tossed 發生在 all night"
        },
        {
            "type": "TimeOfCondition",
            "roles": {
                "Condition": "turned",
                "Time": "all night"
            },
            "text": "turned 發生在 all night"
        },
        {
            "type": "TimeOfCondition",
            "roles": {
                "Condition": "tired",
                "Time": "today"
            },
            "text": "tired 發生在 today"
        },
        {
            "type": "TimeOfCondition",
            "roles": {
                "Condition": "irritable",
                "Time": "today"
            },
            "text": "irritable 發生在 today"
        },
        {
            "type": "TimeOfMedication",
            "roles": {
                "Time": "noon",
                "Medication": "ibuprofen"
            },
            "text": "TimeOfMedication: Time=noon, Medication=ibuprofen"
        },
        {
            "type": "QualifierOfCondition",
            "roles": {
                "Qualifier": "bit",
                "Condition": "relaxed"
            },
            "text": "QualifierOfCondition: Qualifier=bit, Condition=relaxed"
        }
    ]
}