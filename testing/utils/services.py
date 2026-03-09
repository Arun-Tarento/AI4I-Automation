"""
Centralized test data for all AI services

"""
import sys
import json
from pathlib import Path
# API_DIR = Path(__file__).parent
# sys.path.insert(0, str(API_DIR))
from config.settings import settings
from utils.helper import audio_to_base64, image_to_base64


class ServiceWithPayloads:
    """Centralized test payloads for all AI services"""
    SAMPLES_DIR = Path(__file__).parent.parent/"samples"
    NMT_SAMPLES_DIR = SAMPLES_DIR/"nmt"
    ASR_SAMPLES_DIR = SAMPLES_DIR/"asr"
    TTS_SAMPLES_DIR = SAMPLES_DIR/"tts" 
    TRANSLITERATION_SAMPLES_DIR = SAMPLES_DIR/"transliteration"
    TEXT_LANGUAGE_DETECTION_SAMPLES_DIR = SAMPLES_DIR/"text_language_detection" 
    SPEAKER_DIARIZATION_SAMPLES_DIR = SAMPLES_DIR/"speaker_diarization"
    LANGUAGE_DIARIZATION_SAMPLES_DIR = SAMPLES_DIR/"language_diarization"
    AUDIO_LANGUAGE_DETECTION_SAMPLES_DIR = SAMPLES_DIR/"audio_language_detection"
    NER_SAMPLES_DIR = SAMPLES_DIR/"ner" 
    OCR_SAMPLES_DIR = SAMPLES_DIR/"ocr"
    PIPELINE_SAMPLES_DIR = SAMPLES_DIR/"pipeline"


    @staticmethod
    def nmt(source_text=None, source_lang="hi", target_lang="ta", data_tracking=False, service_id=None):
        """
        NMT translation payload
         
        Args:
            source_text: Text to translate. If None, loads from nmt_sample.json
            source_lang: Source language code (default: hi)
            target_lang: Target language code (default: ta)
            data_tracking: Enable data tracking (default: False)
        
        Returns:
            dict: NMT inference payload
        """
        # If no source_text provided, load from sample file
        if source_text is None:
            sample_file = ServiceWithPayloads.NMT_SAMPLES_DIR / "nmt_sample.json"
            with open(sample_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                source_text = data.get("input", "Sample text")  # Adjust based on your JSON structure
        
        return {
            "input": [{"source": source_text}],
            "config": {
                "language": {
                    "sourceLanguage": source_lang,
                    "targetLanguage": target_lang
                },
                "serviceId": service_id if service_id else settings.NMT_SERVICE_ID
            },
            "controlConfig": {
                "dataTracking": data_tracking
            }
        }

    @staticmethod
    def nmt_without_service_id(source_text=None, source_lang="hi", target_lang="ta", data_tracking=False):
        """NMT payload without serviceId - for negative testing"""
        if source_text is None:
            sample_file = ServiceWithPayloads.NMT_SAMPLES_DIR / "nmt_sample.json"
            with open(sample_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                source_text = data.get("input", "Sample text")
        
        return {
            "input": [{"source": source_text}],
            "config": {
                "language": {
                    "sourceLanguage": source_lang,
                    "targetLanguage": target_lang
                }
                # serviceId intentionally omitted
            },
            "controlConfig": {
                "dataTracking": data_tracking
            }
        }

    @staticmethod
    def nmt_with_context_aware(source_text=None, source_lang="hi", target_lang="ta", context="general", data_tracking=False, service_id=None):
        """NMT payload with context aware - for Scenario 6
        
        Args:
            context: Context value for LLM inference (e.g. "general", "medical", "legal")
        """
        if source_text is None:
            sample_file = ServiceWithPayloads.NMT_SAMPLES_DIR / "nmt_sample.json"
            with open(sample_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                source_text = data.get("input", "Sample text")
        
        config = {
            "language": {
                "sourceLanguage": source_lang,
                "targetLanguage": target_lang
            }
        }
        
        if context is not None:
            config["context"] = context
        
        if service_id:
            config["serviceId"] = service_id

        return {
            "input": [{"source": source_text}],
            "config": config,
            "controlConfig": {
                "dataTracking": data_tracking
            }
        }

##############################################################################################################################################

    @staticmethod
    def asr(
        audio_file_path=None,
        audio_base64=None,
        source_lang="hi",
        audio_format="mp3",
        sampling_rate=16000,
        transcription_format="transcript",
        best_token_count=0,
        encoding="base64",
        pre_processors=None,
        post_processors=None,
        data_tracking=False
    ):
        """
        ASR inference payload
        
        Args:
            audio_file_path: Path to audio file (relative to samples/asr/ or absolute)
                           If None, uses samples/asr/example.mp3
            audio_base64: Pre-encoded base64 audio (optional, overrides audio_file_path)
            source_lang: Source language code (default: hi)
            audio_format: Audio format (default: mp3)
            sampling_rate: Audio sampling rate (default: 16000)
            transcription_format: Output format (default: transcript)
            best_token_count: Number of best tokens (default: 0)
            encoding: Audio encoding type (default: base64)
            pre_processors: List of preprocessors (default: ["vad", "denoise"])
            post_processors: List of postprocessors (default: ["lm", "punctuation"])
            data_tracking: Enable data tracking (default: False)
        
        Returns:
            dict: ASR inference payload
        """
        # Set default processors
        if pre_processors is None:
            pre_processors = ["vad", "denoise"]
        if post_processors is None:
            post_processors = ["lm", "punctuation"]
        
        # Get audio content as base64
        if audio_base64:
            # Use provided base64
            audio_content = audio_base64
        elif audio_file_path:
            # Convert provided file path to base64
            if not Path(audio_file_path).is_absolute():
                # Relative path from samples/asr/
                audio_file_path = ServiceWithPayloads.ASR_SAMPLES_DIR / audio_file_path
            audio_content = audio_to_base64(str(audio_file_path))
        else:
            # Use default example.mp3
            default_audio = ServiceWithPayloads.ASR_SAMPLES_DIR / "hindi_4s.wav"
            audio_content = audio_to_base64(str(default_audio))
        
        return {
            "audio": [{
                "audioContent": audio_content
            }],
            "config": {
                "language": {
                    "sourceLanguage": source_lang
                },
                "serviceId": settings.ASR_SERVICE_ID,
                "audioFormat": audio_format,
                "samplingRate": sampling_rate,
                "transcriptionFormat": transcription_format,
                "bestTokenCount": best_token_count,
                "encoding": encoding,
                "preProcessors": pre_processors,
                "postProcessors": post_processors
            },
            "controlConfig": {
                "dataTracking": data_tracking
            }
        }


    def tts(source_text=None, source_lang="hi", gender="female", sampling_rate=22050, audio_format="wav", data_tracking=False):
        """
        TTS text-to-speech payload
        
        Args:
            source_text: Text to convert to speech. If None, loads from tts_sample.json
            source_lang: Source language code (default: hi)
            gender: Voice gender - "female" or "male" (default: female)
            sampling_rate: Audio sampling rate (default: 22050)
            audio_format: Output audio format (default: wav)
            data_tracking: Enable data tracking (default: False)
        
        Returns:
            dict: TTS inference payload
        """
        # If no source_text provided, load from sample file
        if source_text is None:
            sample_file = ServiceWithPayloads.TTS_SAMPLES_DIR / "tts_sample.json"
            with open(sample_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                source_text = data["tts_samples"][0]["source"]
        
        return {
            "input": [{"source": source_text}],
            "config": {
                "language": {
                    "sourceLanguage": source_lang
                },
                "serviceId": settings.TTS_SERVICE_ID,
                "gender": gender,
                "samplingRate": sampling_rate,
                "audioFormat": audio_format
            },
            "controlConfig": {
                "dataTracking": data_tracking
            }
        }

    @staticmethod
    def transliteration(source_text=None, source_lang="hi", target_lang="ta", is_sentence=True, num_suggestions=0, data_tracking=False):
        """
        Transliteration payload
        
        Args:
            source_text: Text to transliterate. If None, loads from transliteration_sample.json
            source_lang: Source language code (default: hi)
            target_lang: Target language code (default: ta)
            is_sentence: Whether input is a sentence (default: True)
            num_suggestions: Number of suggestions to return (default: 0)
            data_tracking: Enable data tracking (default: False)
        
        Returns:
            dict: Transliteration inference payload
        """
        # If no source_text provided, load from sample file
        if source_text is None:
            sample_file = ServiceWithPayloads.TRANSLITERATION_SAMPLES_DIR / "transliteration_sample.json"
            with open(sample_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                source_text = data["transliteration_samples"][0]["source"]
        
        return {
            "input": [{"source": source_text}],
            "config": {
                "serviceId": settings.TRANSLITERATION_SERVICE_ID,
                "language": {
                    "sourceLanguage": source_lang,
                    "targetLanguage": target_lang
                },
                "isSentence": is_sentence,
                "numSuggestions": num_suggestions
            },
            "controlConfig": {
                "dataTracking": data_tracking
            }
        }
        
    @staticmethod
    def text_language_detection(source_text=None, data_tracking=False):
        """
        Text Language Detection payload
        
        Args:
            source_text: Text to detect language. If None, loads from text_language_detection_sample.json
            data_tracking: Enable data tracking (default: False)
        
        Returns:
            dict: Text Language Detection inference payload
        """
        # If no source_text provided, load from sample file
        if source_text is None:
            sample_file = ServiceWithPayloads.TEXT_LANGUAGE_DETECTION_SAMPLES_DIR / "text_langage_detection_sample.json" 
            with open(sample_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                source_text = data["text_language_detection_samples"][0]["source"]
        
        return {
            "input": [{"source": source_text}],
            "config": {
                "serviceId": settings.TEXT_LANGUAGE_DETECTION_SERVICE_ID
            },
            "controlConfig": {
                "dataTracking": data_tracking
            }
        } # Easy-to-use helper methods


    @staticmethod
    def speaker_diarization(audio_base64=None, audio_file_path=None, data_tracking=False):
        """
        Speaker Diarization payload
        
        Args:
            audio_base64: Base64 encoded audio. If provided, uses this directly
            audio_file_path: Path to audio file. If None, uses default hindi_4s.wav
            data_tracking: Enable data tracking (default: False)
    
        Returns:
            dict: Speaker Diarization inference payload
        """
        if audio_base64:
            # Use provided base64
            audio_content = audio_base64
        elif audio_file_path:
            # Convert provided file path to base64
            if not Path(audio_file_path).is_absolute():
                # Relative path from samples/speaker_diarization/
                audio_file_path = ServiceWithPayloads.SPEAKER_DIARIZATION_SAMPLES_DIR / audio_file_path
            audio_content = audio_to_base64(str(audio_file_path))
        else:
            # Use default hindi_4s.wav
            default_audio = ServiceWithPayloads.SPEAKER_DIARIZATION_SAMPLES_DIR / "hindi_4s.wav"
            audio_content = audio_to_base64(str(default_audio))
    
        payload = {
            "audio": [
                {
                    "audioContent": audio_content
                }
            ],
            "config": {
                "serviceId": settings.SPEAKER_DIARIZATION_SERVICE_ID
            },
            "controlConfig": {
                "dataTracking": data_tracking
            }
        }
        
        return payload  

    @staticmethod
    def language_diarization(audio_base64=None, audio_file_path=None, data_tracking=False):
        """
        Language Diarization payload
        
        Args:
            audio_base64: Base64 encoded audio. If provided, uses this directly
            audio_file_path: Path to audio file. If None, uses default hindi_4s.wav
            data_tracking: Enable data tracking (default: False)
        
        Returns:
            dict: Language Diarization inference payload
        """
        if audio_base64:
            # Use provided base64
            audio_content = audio_base64
        elif audio_file_path:
            # Convert provided file path to base64
            if not Path(audio_file_path).is_absolute():
                # Relative path from samples/language_diarization/
                audio_file_path = ServiceWithPayloads.LANGUAGE_DIARIZATION_SAMPLES_DIR / audio_file_path
            audio_content = audio_to_base64(str(audio_file_path))
        else:
            # Use default hindi_4s.wav
            default_audio = ServiceWithPayloads.LANGUAGE_DIARIZATION_SAMPLES_DIR / "hindi_4s.wav"
            audio_content = audio_to_base64(str(default_audio))
        
        payload = {
            "audio": [
                {
                    "audioContent": audio_content
                }
            ],
            "config": {
                "serviceId": settings.LANGUAGE_DIARIZATION_SERVICE_ID
            },
            "controlConfig": {
                "dataTracking": data_tracking
            }
        }
        
        return payload                                                                       

    @staticmethod
    def audio_language_detection(audio_base64=None, audio_file_path=None, data_tracking=False):
        """
        Audio Language Detection payload
        
        Args:
            audio_base64: Base64 encoded audio. If provided, uses this directly
            audio_file_path: Path to audio file. If None, uses default hindi_4s.wav
            data_tracking: Enable data tracking (default: False)
        
        Returns:
            dict: Audio Language Detection inference payload
        """
        if audio_base64:
            # Use provided base64
            audio_content = audio_base64
        elif audio_file_path:
            # Convert provided file path to base64
            if not Path(audio_file_path).is_absolute():
                # Relative path from samples/audio_language_detection/
                audio_file_path = ServiceWithPayloads.AUDIO_LANGUAGE_DETECTION_SAMPLES_DIR / audio_file_path
            audio_content = audio_to_base64(str(audio_file_path))
        else:
            # Use default hindi_4s.wav
            default_audio = ServiceWithPayloads.AUDIO_LANGUAGE_DETECTION_SAMPLES_DIR / "hindi_4s.wav"
            audio_content = audio_to_base64(str(default_audio))
        
        payload = {
            "audio": [
                {
                    "audioContent": audio_content
                }
            ],
            "config": {
                "serviceId": settings.AUDIO_LANGUAGE_DETECTION_SERVICE_ID
            },
            "controlConfig": {
                "dataTracking": data_tracking
            }
        }
        
        return payload    


    @staticmethod
    def ner(source_text=None, source_lang="hi", data_tracking=False):
        """
        NER (Named Entity Recognition) payload
        
        Args:
            source_text: Text for entity recognition. If None, loads from ner_sample.json
            source_lang: Source language code (default: hi)
            data_tracking: Enable data tracking (default: False)
        
        Returns:
            dict: NER inference payload
        """
        # If no source_text provided, load from sample file
        if source_text is None:
            sample_file = ServiceWithPayloads.NER_SAMPLES_DIR / "ner_sample.json"
            # print(f"🔍 DEBUG - Sample file path: {sample_file}")
            # print(f"🔍 DEBUG - File exists: {sample_file.exists()}")
            with open(sample_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                source_text = data["ner_samples"][0]["source"]
        
        return {
            "input": [{"source": source_text}],
            "config": {
                "serviceId": settings.NER_SERVICE_ID,
                "language": {
                    "sourceLanguage": source_lang
                }
            },
            "controlConfig": {
                "dataTracking": data_tracking
            }
        }

    @staticmethod
    def ocr(image_base64=None, image_file_path=None, source_lang="en", script_code="", text_detection=True, data_tracking=True):
        """
        OCR (Optical Character Recognition) payload
        
        Args:
            image_base64: Base64 encoded image. If provided, uses this directly
            image_file_path: Path to image file. If None, uses default OCR_HINDI_JPEG.jpg
            source_lang: Source language code (default: en)
            script_code: Source script code (default: "")
            text_detection: Enable text detection (default: True)
            data_tracking: Enable data tracking (default: True)
        
        Returns:
            dict: OCR inference payload
        """
        if image_base64:
            # Use provided base64
            image_content = image_base64
        elif image_file_path:
            # Convert provided file path to base64
            if not Path(image_file_path).is_absolute():
                # Relative path from samples/ocr/
                image_file_path = ServiceWithPayloads.OCR_SAMPLES_DIR / image_file_path
            image_content = image_to_base64(str(image_file_path))
        else:
            # Use default OCR_HINDI_JPEG.jpg
            default_image = ServiceWithPayloads.OCR_SAMPLES_DIR / "OCR_HINDI_JPEG.jpg"
            image_content = image_to_base64(str(default_image))
        
        payload = {
            "image": [
                {
                    "imageContent": image_content,
                    "imageUri": None
                }
            ],
            "config": {
                "serviceId": settings.OCR_SERVICE_ID,
                "language": {
                    "sourceLanguage": source_lang,
                    "sourceScriptCode": script_code
                },
                "textDetection": text_detection
            },
            "controlConfig": {
                "dataTracking": data_tracking
            }
        }
        
        return payload                                                                                                 
    
    @staticmethod
    def pipeline(audio_base64=None, audio_file_path=None, source_lang="hi", target_lang="mr", tts_gender="male", data_tracking=False):
        """
        Pipeline payload (ASR → Translation → TTS)
        
        Args:
            audio_base64: Base64 encoded audio. If provided, uses this directly
            audio_file_path: Path to audio file. If None, uses default hindi_4s.wav
            source_lang: Source language code (default: hi)
            target_lang: Target language code (default: mr)
            tts_gender: TTS voice gender (default: male)
            data_tracking: Enable data tracking (default: False)
        
        Returns:
            dict: Pipeline inference payload
        """
        if audio_base64:
            # Use provided base64
            audio_content = audio_base64
        elif audio_file_path:
            # Convert provided file path to base64
            if not Path(audio_file_path).is_absolute():
                # Relative path from samples/pipeline/
                audio_file_path = ServiceWithPayloads.PIPELINE_SAMPLES_DIR / audio_file_path
            audio_content = audio_to_base64(str(audio_file_path))
        else:
            # Use default hindi_4s.wav
            default_audio = ServiceWithPayloads.PIPELINE_SAMPLES_DIR / "hindi_4s.wav"
            audio_content = audio_to_base64(str(default_audio))
        
        payload = {
            "pipelineTasks": [
                {
                    "taskType": "asr",
                    "config": {
                        "serviceId": settings.ASR_SERVICE_ID,
                        "language": {
                            "sourceLanguage": source_lang
                        },
                        "audioFormat": "wav",
                        "preProcessors": ["vad", "denoiser"],
                        "postProcessors": ["lm", "punctuation"],
                        "transcriptionFormat": "transcript"
                    }
                },
                {
                    "taskType": "translation",
                    "config": {
                        "serviceId": settings.NMT_SERVICE_ID,
                        "language": {
                            "sourceLanguage": source_lang,
                            "targetLanguage": target_lang
                        }
                    }
                },
                {
                    "taskType": "tts",
                    "config": {
                        "serviceId": settings.TTS_SERVICE_ID,
                        "language": {
                            "sourceLanguage": target_lang
                        },
                        "gender": tts_gender
                    }
                }
            ],
            "inputData": {
                "audio": [
                    {
                        "audioContent": audio_content
                    }
                ]
            },
            "controlConfig": {
                "dataTracking": data_tracking
            }
        }
        
        return payload


############################################CONVENIENCE FROM_SAMPLE METHODS###############################################################
    @staticmethod
    def nmt_from_sample():
        """Load NMT payload with text from nmt_sample.json"""
        return ServiceWithPayloads.nmt()


    
    @staticmethod
    def asr_from_sample():
        """Load ASR payload with audio from example.mp3"""
        return ServiceWithPayloads.asr()


    @staticmethod
    def tts_from_sample():
        """Load TTS payload with text from tts_sample.json"""
        return ServiceWithPayloads.tts()

    @staticmethod
    def transliteration_from_sample():
        """Load Transliteration payload with text from transliteration_sample.json"""
        return ServiceWithPayloads.transliteration()

    @staticmethod
    def text_language_detection_from_sample():
        """Load Text Language Detection payload with text from text_language_detection_sample.json"""
        return ServiceWithPayloads.text_language_detection()

    @staticmethod
    def speaker_diarization_from_sample():
        """Load Speaker Diarization payload with audio from hindi_4s.wav"""
        return ServiceWithPayloads.speaker_diarization()

    @staticmethod
    def language_diarization_from_sample():
        """Load Language Diarization payload with audio from hindi_4s.wav"""
        return ServiceWithPayloads.language_diarization()  

    @staticmethod
    def audio_language_detection_from_sample():
        """Load Audio Language Detection payload with audio from hindi_4s.wav"""
        return ServiceWithPayloads.audio_language_detection()   

    @staticmethod
    def ner_from_sample():
        """Load NER payload with text from ner_sample.json"""
        return ServiceWithPayloads.ner()
    
    @staticmethod
    def ocr_from_sample():
        """Load OCR payload with image from OCR_HINDI_JPEG.jpg"""
        return ServiceWithPayloads.ocr()

    @staticmethod
    def pipeline_from_sample():
        """Load Pipeline payload with audio from hindi_4s.wav"""
        return ServiceWithPayloads.pipeline()

##################################################### MODEL MANAGEMENT ############################################################################
    @staticmethod
    def model_name(role_name: str, timestamp: int, task_type: str = None) -> str:
        """
            Generate a unique model name
            Args:
                role_name: Role name e.g. 'admin', 'moderator'
                timestamp: Unix timestamp
                task_type: Optional task type e.g. 'asr', 'nmt'
            Returns:
                str: Unique model name
            """
        if task_type:
            return f"Test-Model-{task_type}-{role_name.lower()}-{timestamp}"
        return f"Test-Model-{role_name.lower()}-{timestamp}"


    @staticmethod
    def model_create_payload(name: str, version: str, task_type: str = "asr") -> dict:
        """
        Model Management - Create Model payload

        Args:
            name: Model name (mandatory, must be unique with version)
            version: Model version (mandatory, must be unique with name)
            task_type: Task type - "asr", "nmt", or "tts" (default: "asr")

        Returns:
            dict: Create model payload
        """
        return {
            "modelId": "Example/Example-1",
            "version": version,
            "name": name,
            "description": "A sample model for demonstration purposes",
            "refUrl": "https://github.com/example/example-model",
            "task": {
                "type": task_type
            },
            "languages": [
                {
                    "sourceLanguage": "hi",
                    "sourceScriptCode": "Deva",
                    "targetLanguage": "hi",
                    "targetScriptCode": "Deva"
                }
            ],
            "license": "mit",
            "domain": ["general"],
            "inferenceEndPoint": {
                "schema": {
                    "modelProcessingType": {
                        "type": "batch"
                    },
                    "request": {
                        "input": [{"audio": "base64_encoded_audio_string"}],
                        "config": {
                            "language": {"sourceLanguage": "hi"}
                        }
                    },
                    "response": {
                        "output": [{"transcript": "string"}]
                    }
                }
            },
            "benchmarks": [
                {
                    "benchmarkId": "example-benchmark-001",
                    "name": "Example Benchmark",
                    "description": "Sample benchmark for evaluation",
                    "domain": "general",
                    "createdOn": "2025-01-15T10:00:00.000Z",
                    "languages": {
                        "sourceLanguage": "hi",
                        "targetLanguage": "hi"
                    },
                    "score": [{"metricName": "WER", "score": "7.5"}]
                }
            ],
            "submitter": {
                "name": "Example Organization",
                "aboutMe": "An example organization",
                "team": [
                    {
                        "name": "John Doe",
                        "aboutMe": "Lead Researcher",
                        "oauthId": {
                            "oauthId": "1234567890",
                            "provider": "google"
                        }
                    }
                ]
            }
        }

    @staticmethod
    def model_create_payload_from_sample(role_name: str = "admin", 
                                        task_type: str = "asr",
                                        timestamp: int = None) -> dict:
        import time
        if timestamp is None:
            timestamp = int(time.time())
        return ServiceWithPayloads.model_create_payload(
            name=ServiceWithPayloads.model_name(
                role_name=role_name,
                timestamp=timestamp,
                task_type=task_type
            ),
            version="1.0.0",
            task_type=task_type
        )

    @staticmethod
    def model_update_payload(model_id: str, uuid: str, version: str, 
                            task_type: str = "asr", 
                            version_status: str = "ACTIVE",
                            license: str = "MIT") -> dict:
        """
        Model Management - Update Model payload (PATCH)

        Args:
            model_id: Model ID to locate the model (mandatory)
            uuid: Model UUID (mandatory)
            version: Model version to locate the model (mandatory)
            task_type: Task type (default: asr)
            version_status: ACTIVE or DEPRECATED (default: ACTIVE)
            license: Valid license string (default: MIT)

        Returns:
            dict: Update model payload
        """
        return {
            "modelId": model_id,
            "uuid": uuid,
            "version": version,
            "versionStatus": version_status,
            "description": "A sample model for demonstration purposes",
            "languages": [
                {
                    "sourceLanguage": "hi",
                    "targetLanguage": "hi",
                    "sourceScriptCode": "Deva",
                    "targetScriptCode": "Deva"
                }
            ],
            "domain": ["general"],
            "submitter": {
                "name": "Example Organization",
                "aboutMe": "An example organization",
                "team": [
                    {
                        "name": "John Doe",
                        "aboutMe": "Lead Researcher",
                        "oauthId": {
                            "oauthId": "1234567890",
                            "provider": "google"
                        }
                    }
                ]
            },
            "license": license,
            "inferenceEndPoint": {
                "schema": {
                    "modelProcessingType": {
                        "type": "batch"
                    },
                    "model_name": None,
                    "request": {
                        "input": [{"audio": "base64_encoded_audio_string"}],
                        "config": {
                            "language": {"sourceLanguage": "hi"}
                        }
                    },
                    "response": {
                        "output": [{"transcript": "string"}]
                    }
                },
                "endpoint": None,
                "model_name": None,
                "modelName": None,
                "model": None
            },
            "source": "https://github.com/example/example-model",
            "task": {
                "type": task_type
            }
        }


##########################################################################Services##########################################################################
    @staticmethod
    def service_name(prefix: str, role_name: str, timestamp: int) -> str:
        """
        Generate a unique service name compliant with alphanumeric + hyphens rule
        Args:
            prefix: Short descriptor e.g. 'svc', 'no-modelid', 'deprecated'
            role_name: Role name e.g. 'admin', 'moderator'
            timestamp: Unix timestamp
        Returns:
            str: Unique service name
        """
        return f"test-svc-{prefix}-{role_name.lower()}-{timestamp}"

    @staticmethod
    def service_create_payload(model_id: str,
                                model_version: str,
                                service_name: str,
                                service_description: str = "Test service description",
                                hardware_description: str = "Test hardware description",
                                endpoint: str = "http://test-endpoint:8000",
                                api_key: str = "test-api-key",
                                is_published: bool = False) -> dict:
        """
        Model Management - Create Service payload

        Args:
            model_id: Model ID to link the service to (mandatory)
            model_version: Model version (mandatory)
            service_name: Name of the service - alphanumeric + hyphens only (mandatory)
            service_description: Service description (mandatory)
            hardware_description: Hardware description
            endpoint: Service endpoint URL (mandatory)
            api_key: API key for the service
            is_published: Publish status (default: False)

        Returns:
            dict: Create service payload
        """
        return {
            "name": service_name,
            "serviceDescription": service_description,
            "hardwareDescription": hardware_description,
            "publishedOn": 0,
            "modelId": model_id,
            "modelVersion": model_version,
            "endpoint": endpoint,
            "api_key": api_key,
            "isPublished": is_published
        }

    @staticmethod
    def service_update_payload(service_id: str,
                                service_description: str = "Updated service description",
                                hardware_description: str = "Updated hardware description",
                                is_published: bool = False) -> dict:
        """
        Model Management - Update Service payload (PATCH)

        Args:
            service_id: Service ID to locate the service (mandatory)
            service_description: Updated service description
            hardware_description: Updated hardware description
            is_published: Publish/unpublish the service (default: False)

        Returns:
            dict: Update service payload
        """
        return {
            "serviceId": service_id,
            "serviceDescription": service_description,
            "hardwareDescription": hardware_description,
            "isPublished": is_published
        }