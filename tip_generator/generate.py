import os
from litellm import completion
from litellm.exceptions import APIError

from pathlib import Path
from dotenv import load_dotenv
import sys
import json

from loguru import logger

load_dotenv()
logger.remove()
logger.add(sys.stdout, level="INFO")

# format output by calling function
tools = [
    {
        "type": "function",
        "function": {
            "name": "format_output",
            "description": "A function that formats a recommendation and their additional information properly",
            "parameters": {
                "type": "object",
                "properties": {
                    "recommendation_set": {
                        "type": "array",
                        "description": "A set that contains a recommendation and all additional information.",
                        "items": {
                            "type": "object",
                            "properties": {
                                "short_desc": {
                                    "type": "string",
                                    "description": "Write the concise tip based on the input text; precise, concrete, 50–200 characters."
                                },
                                "long_desc": {
                                    "type": "string",
                                    "description": "Introduce the study using indefinite pronouns, max 500 characters, include names and dates in a flowing text."
                                },
                                "goal": {
                                    "type": "string",
                                    "enum": ["augment", "prevent", "recover", "maintain"],
                                    "description": "Choose the goal type for the recommendation."
                                },
                                "activity_type": {
                                    "type": "string",
                                    "enum": ["creative", "exercise", "cognitive", "relax", "social", "time management", "nutrition"],
                                    "description": "Select the main activity type the tip requires."
                                },
                                "categories": {
                                    "type": "array",
                                    "items": {
                                        "type": "string",
                                        "enum": [
                                            "work", "success", "productivity", "performance", "focus",
                                            "time management", "happiness", "mental", "active reflection",
                                            "awareness", "well-being", "health", "fitness", "social"
                                        ]
                                    },
                                    "description": "Assign one or more relevant categories."
                                },
                                "concerns": {
                                    "type": "array",
                                    "items": {
                                        "type": "string",
                                        "enum": [
                                            "goal-setting", "self-motivation", "self-direction", "self-discipline",
                                            "focus", "mindeset", "time management", "procrastination", "stress management",
                                            "mental-health", "work-life balance", "sleep quality"
                                        ]
                                    },
                                    "description": "Assign relevant concerns the tip addresses."
                                },
                                "daytime": {
                                    "type": "string",
                                    "enum": ["morning", "noon", "evening", "end of day", "any"],
                                    "description": "Best time of day for tip execution."
                                },
                                "weekdays": {
                                    "type": "string",
                                    "enum": ["workdays", "weekend", "week start", "end of workweek", "public holiday", "any"],
                                    "description": "When the tip is most relevant during the week."
                                },
                                "season": {
                                    "type": "string",
                                    "enum": ["any", "spring", "summer", "autumn", "winter", "holiday season", "summer vacation"],
                                    "description": "Best seasonal context for tip execution."
                                },
                                "is_outdoor": {
                                    "type": "boolean",
                                    "description": "TRUE,if tip is best done outdoors. FALSE, if indoors or both are suitable."
                                },
                                "is_basic": {
                                    "type": "boolean",
                                    "description": "TRUE if suitable for users with low health literacy."
                                },
                                "is_advanced": {
                                    "type": "boolean",
                                    "description": "TRUE if tip is for users with advanced/high health literacy."
                                },
                                "gender": {
                                    "type": "string",
                                    "enum": ["any", "male", "female"],
                                    "description": "Gender relevance of the tip."
                                }
                            },
                            "required": [
                                "short_desc", "long_desc", "goal", "activity_type", "categories",
                                "concerns", "daytime", "weekdays", "season", "is_outdoor",
                                "is_basic", "is_advanced", "gender"
                            ]
                        }
                    }
                }
            }
        }
    }
]


def generate_recommendations(input_text: str, modelname : str = os.getenv("REC_GENERATION_MODEL"), instruction_file: str = os.getenv("REC_GENERATION_INSTRUCTIONS")) -> dict:
    try:
        with Path(instruction_file).absolute().resolve().open(encoding='utf-8', errors='replace') as f:
            instruction_text = f.read()
    except FileNotFoundError as e:
        raise FileNotFoundError(f"File not found: {e}")
    except PermissionError as e:
        raise PermissionError(f"Permission for instruction denied: {e}")
    except Exception as e:
        raise Exception(f"Unexpected error occured: {e}")

    # completion
    try:
        logger.info("Processing input text...")
        response = completion(
            model=modelname,
            messages=[
                {'role': 'system', 'content': instruction_text},
                {'role': 'user', 'content': f'Extract recommendations out of this paper: {input_text}'}
            ],
            tools=tools,
            # Not yet tested in detail (TODO), but th assumption is:
            # set top_p low to get more accurate results and prevent from getting too many (redundant) recommendations and hallucinations
            # keep temperature high to get more creative expressions, but not too high to prevent from deviating too much from the input text
            temperature=0.7,
            top_p=0.1
        )
    except KeyError as e:
        raise KeyError(f"Keyerror: {e}")
    except APIError as e:
        raise APIError(f"API error: {e}")
    except Exception as e:
        raise Exception(f"Unexpected error: {e}")

    # extract completion and create output dictionary
    output = response.to_dict()
    # to keep track of used instruction file
    output["instruction"] = Path(instruction_file).stem
    output["output"] = [json.loads(c.function.arguments)
                        for c in response.choices[0].message.tool_calls]

    logger.info(f"{len(output['output'])} recommendations generated successfully.")
    return output