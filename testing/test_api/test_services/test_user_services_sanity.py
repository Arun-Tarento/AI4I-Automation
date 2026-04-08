"""
E2E tests for USER role with AI4I services.
Tests RBAC permissions for USER role with valid and invalid API keys.
"""

import pytest
from utils.services import ServiceWithPayloads


class TestUserServicesWithValidAPIKey:
    """Test USER role access to AI services with valid API key"""
    
    def test_nmt_services_with_valid_api_key_User(self, user_client_with_valid_api_key):
        """
        User : Test NMT service with valid API key
        """
        endpoint = "/api/v1/nmt/inference"
        payload = ServiceWithPayloads.nmt_from_sample()
        
        response = user_client_with_valid_api_key.post(endpoint, json=payload)
        
        assert response.status_code == 200, (
            f"Expected 200, got {response.status_code}. Response: {response.text}"
        )
        
        data = response.json()
        assert "output" in data
        assert len(data["output"]) > 0
        assert "source" in data["output"][0]
        assert "target" in data["output"][0]
        
        source = data["output"][0]["source"]
        target = data["output"][0]["target"]
        
        print(f"\n✅ USER NMT: '{source}' → '{target}'")

    def test_asr_service_with_valid_api_key_User(self, user_client_with_valid_api_key):
        """
        User : Test ASR service with valid API key
        """
        endpoint = "/api/v1/asr/inference"
        payload = ServiceWithPayloads.asr_from_sample()
        
        response = user_client_with_valid_api_key.post(endpoint, json=payload)
        
        assert response.status_code == 200, (
            f"Expected 200, got {response.status_code}. Response: {response.text}"
        )
        
        data = response.json()
        assert "output" in data
        assert len(data["output"]) > 0
        assert "source" in data["output"][0]
        
        transcript = data["output"][0]["source"]
        
        print(f"\n✅ USER ASR: '{transcript}'")

    def test_tts_service_with_valid_api_key_User(self, user_client_with_valid_api_key):
        """
        User : Test TTS service with valid API key
        """
        endpoint = "/api/v1/tts/inference"
        payload = ServiceWithPayloads.tts_from_sample()
        
        response = user_client_with_valid_api_key.post(endpoint, json=payload)
        
        assert response.status_code == 200, (
            f"Expected 200, got {response.status_code}. Response: {response.text}"
        )
        
        data = response.json()
        assert "audio" in data
        assert len(data["audio"]) > 0
        assert "audioContent" in data["audio"][0]
        assert data["audio"][0]["audioContent"]
        
        source_text = payload["input"][0]["source"][:50]
        audio_content = data["audio"][0]["audioContent"]
        
        print(f"\n✅ USER TTS: Generated audio for '{source_text}...'")
        print(f"   Audio length: {len(audio_content)} characters")

    def test_transliteration_service_with_valid_api_key_User(self, user_client_with_valid_api_key):
        """
        User : Test Transliteration service with valid API key
        """
        endpoint = "/api/v1/transliteration/inference"
        payload = ServiceWithPayloads.transliteration_from_sample()
        
        response = user_client_with_valid_api_key.post(endpoint, json=payload)
        
        assert response.status_code == 200, (
            f"Expected 200, got {response.status_code}. Response: {response.text}"
        )
        
        data = response.json()
        assert "output" in data
        assert len(data["output"]) > 0
        assert "source" in data["output"][0]
        assert "target" in data["output"][0]
        
        source = data["output"][0]["source"]
        target = data["output"][0]["target"]
        
        print(f"\n✅ USER Transliteration: '{source}' → '{target}'")

    def test_text_language_detection_services_with_valid_api_key_User(self, user_client_with_valid_api_key):
        """
        User : Test Text Language Detection service with valid API key
        """
        endpoint = "/api/v1/language-detection/inference"
        payload = ServiceWithPayloads.text_language_detection_from_sample()
        
        response = user_client_with_valid_api_key.post(endpoint, json=payload)
        
        assert response.status_code == 200, (
            f"Expected 200, got {response.status_code}. Response: {response.text}"
        )
        
        data = response.json()
        assert "output" in data
        assert len(data["output"]) > 0
        assert "source" in data["output"][0]
        assert "langPrediction" in data["output"][0]
        assert len(data["output"][0]["langPrediction"]) > 0
        assert "langCode" in data["output"][0]["langPrediction"][0]
        assert "language" in data["output"][0]["langPrediction"][0]
        
        source = data["output"][0]["source"]
        detected_lang = data["output"][0]["langPrediction"][0]["language"]
        lang_code = data["output"][0]["langPrediction"][0]["langCode"]
        
        print(f"\n✅ USER Text Language Detection: '{source}'")
        print(f"   Detected: {detected_lang} ({lang_code})")

    def test_speaker_diarization_services_with_valid_api_key_User(self, user_client_with_valid_api_key):
        """
        User : Test Speaker Diarization service with valid API key
        """
        endpoint = "/api/v1/speaker-diarization/inference"
        payload = ServiceWithPayloads.speaker_diarization_from_sample()
        
        response = user_client_with_valid_api_key.post(endpoint, json=payload)
        
        assert response.status_code == 200, (
            f"Expected 200, got {response.status_code}. Response: {response.text}"
        )
        
        data = response.json()
        assert "output" in data
        assert len(data["output"]) > 0
        assert "num_speakers" in data["output"][0]
        assert "total_segments" in data["output"][0]
        assert "speakers" in data["output"][0]
        assert "segments" in data["output"][0]
        assert len(data["output"][0]["segments"]) > 0
        
        num_speakers = data["output"][0]["num_speakers"]
        total_segments = data["output"][0]["total_segments"]
        speakers = ", ".join(data["output"][0]["speakers"])
        
        print(f"\n✅ USER Speaker Diarization:")
        print(f"   Speakers: {num_speakers} ({speakers})")
        print(f"   Total segments: {total_segments}")

    def test_language_diarization_services_with_valid_api_key_User(self, user_client_with_valid_api_key):
        """
        User : Test Language Diarization service with valid API key
        """
        endpoint = "/api/v1/language-diarization/inference"
        payload = ServiceWithPayloads.language_diarization_from_sample()
        
        response = user_client_with_valid_api_key.post(endpoint, json=payload)
        
        assert response.status_code == 200, (
            f"Expected 200, got {response.status_code}. Response: {response.text}"
        )
        
        data = response.json()
        assert "output" in data
        assert len(data["output"]) > 0
        assert "total_segments" in data["output"][0]
        assert "segments" in data["output"][0]
        assert "target_language" in data["output"][0]
        
        total_segments = data["output"][0]["total_segments"]
        target_language = data["output"][0]["target_language"]
        
        print(f"\n✅ USER Language Diarization:")
        print(f"   Total segments: {total_segments}")
        print(f"   Target language: {target_language if target_language else 'None'}")

    def test_audio_language_detection_services_with_valid_api_key_User(self, user_client_with_valid_api_key):
        """
        User : Test Audio Language Detection service with valid API key
        """
        endpoint = "/api/v1/audio-lang-detection/inference"
        payload = ServiceWithPayloads.audio_language_detection_from_sample()
        
        response = user_client_with_valid_api_key.post(endpoint, json=payload)
        
        assert response.status_code == 200, (
            f"Expected 200, got {response.status_code}. Response: {response.text}"
        )
        
        data = response.json()
        assert "output" in data
        assert len(data["output"]) > 0
        assert "language_code" in data["output"][0]
        assert "confidence" in data["output"][0]
        assert "all_scores" in data["output"][0]
        
        language_code = data["output"][0]["language_code"]
        confidence = data["output"][0]["confidence"]
        
        print(f"\n✅ USER Audio Language Detection:")
        print(f"   Detected: {language_code}")
        print(f"   Confidence: {confidence:.2%}")

    def test_ner_services_with_valid_api_key_User(self, user_client_with_valid_api_key):
        """
        User : Test NER service with valid API key
        """
        endpoint = "/api/v1/ner/inference"
        payload = ServiceWithPayloads.ner_from_sample()
        
        response = user_client_with_valid_api_key.post(endpoint, json=payload)
        
        assert response.status_code == 200, (
            f"Expected 200, got {response.status_code}. Response: {response.text}"
        )
        
        data = response.json()
        assert "output" in data
        assert len(data["output"]) > 0
        assert "source" in data["output"][0]
        assert "nerPrediction" in data["output"][0]
        assert len(data["output"][0]["nerPrediction"]) > 0
        
        source = data["output"][0]["source"][:50]
        predictions = data["output"][0]["nerPrediction"]
        total_tokens = len(predictions)
        
        entities = [p for p in predictions if p.get("tag") != "O"]
        entity_count = len(entities)
        
        print(f"\n✅ USER NER: '{source}...'")
        print(f"   Total tokens: {total_tokens}, Entities found: {entity_count}")

    def test_ocr_services_with_valid_api_key_User(self, user_client_with_valid_api_key):
        """
        User : Test OCR service with valid API key
        """
        endpoint = "/api/v1/ocr/inference"
        payload = ServiceWithPayloads.ocr_from_sample()
        
        response = user_client_with_valid_api_key.post(endpoint, json=payload)
        
        assert response.status_code == 200, (
            f"Expected 200, got {response.status_code}. Response: {response.text}"
        )
        
        data = response.json()
        assert "output" in data
        assert len(data["output"]) > 0
        assert "source" in data["output"][0]
        
        extracted_text = data["output"][0]["source"]
        text_preview = extracted_text[:100] if len(extracted_text) > 100 else extracted_text
        
        print(f"\n✅ USER OCR: Extracted text from image")
        print(f"   Preview: {text_preview}...")
        print(f"   Total characters: {len(extracted_text)}")

    def test_pipeline_services_with_valid_api_key_User(self, user_client_with_valid_api_key):
        """
        User : Test Pipeline service with valid API key (ASR → Translation → TTS)
        """
        endpoint = "/api/v1/pipeline/inference"
        payload = ServiceWithPayloads.pipeline_from_sample()
        
        response = user_client_with_valid_api_key.post(endpoint, json=payload)
        
        assert response.status_code == 200, (
            f"Expected 200, got {response.status_code}. Response: {response.text}"
        )
        
        data = response.json()
        print(data)
        assert "pipelineResponse" in data
        assert len(data["pipelineResponse"]) == 3, "Expected 3 pipeline tasks"
        
        # Validate ASR task
        asr_task = data["pipelineResponse"][0]
        assert asr_task["taskType"] == "asr"
        assert "output" in asr_task
        assert len(asr_task["output"]) > 0
        assert "source" in asr_task["output"][0]
        asr_text = asr_task["output"][0]["source"]
        
        # Validate Translation task
        translation_task = data["pipelineResponse"][1]
        assert translation_task["taskType"] == "translation"
        assert "output" in translation_task
        assert len(translation_task["output"]) > 0
        assert "source" in translation_task["output"][0]
        assert "target" in translation_task["output"][0]
        translated_text = translation_task["output"][0]["target"]
        
        # Validate TTS task
        tts_task = data["pipelineResponse"][2]
        assert tts_task["taskType"] == "tts"
        assert "audio" in tts_task or "output" in tts_task
        
        # Check for audio content in either location
        if "audio" in tts_task and tts_task["audio"]:
            assert "audioContent" in tts_task["audio"][0]
            audio_content = tts_task["audio"][0]["audioContent"]
        elif "output" in tts_task and tts_task["output"]:
            assert "audioContent" in tts_task["output"][0]
            audio_content = tts_task["output"][0]["audioContent"]
        else:
            raise AssertionError("No audio content found in TTS task")
        
        print(f"\n✅ USER Pipeline (ASR → Translation → TTS):")
        print(f"   ASR: '{asr_text}'")
        print(f"   Translation: '{translated_text}'")
        print(f"   TTS: Generated audio ({len(audio_content)} chars)")


class TestUserServicesWithInvalidAPIKey:
    """Test USER role access to AI services with invalid API key"""
    
    def test_nmt_services_with_invalid_api_key_User(self, user_client_with_expired_api_key):
        """
        User : Test NMT service with invalid API key
        """
        endpoint = "/api/v1/nmt/inference"
        payload = ServiceWithPayloads.nmt_from_sample()
        
        response = user_client_with_expired_api_key.post(endpoint, json=payload)
        
        assert response.status_code in [401, 403], (
            f"Expected 401/403, got {response.status_code}. Response: {response.text}"
        )
        
        data = response.json()
        assert "detail" in data
        
        print(f"\n✅ USER NMT correctly blocked with invalid key")
        print(f"   Error: {data['detail']}")

    def test_asr_service_with_invalid_api_key_User(self, user_client_with_expired_api_key):
        """
        User : Test ASR service with invalid API key
        """
        endpoint = "/api/v1/asr/inference"
        payload = ServiceWithPayloads.asr_from_sample()
        
        response = user_client_with_expired_api_key.post(endpoint, json=payload)
        
        assert response.status_code in [401, 403], (
            f"Expected 401/403, got {response.status_code}. Response: {response.text}"
        )
        
        data = response.json()
        assert "detail" in data
        
        print(f"\n✅ USER ASR correctly blocked with invalid key")
        print(f"   Error: {data['detail']}")

    def test_tts_service_with_invalid_api_key_User(self, user_client_with_expired_api_key):
        """
        User : Test TTS service with invalid API key
        """
        endpoint = "/api/v1/tts/inference"
        payload = ServiceWithPayloads.tts_from_sample()
        
        response = user_client_with_expired_api_key.post(endpoint, json=payload)
        
        assert response.status_code in [401, 403], (
            f"Expected 401/403, got {response.status_code}. Response: {response.text}"
        )
        
        data = response.json()
        assert "detail" in data
        
        print(f"\n✅ USER TTS correctly blocked with invalid key")
        print(f"   Error: {data['detail']}")

    def test_transliteration_service_with_invalid_api_key_User(self, user_client_with_expired_api_key):
        """
        User : Test Transliteration service with invalid API key
        """
        endpoint = "/api/v1/transliteration/inference"
        payload = ServiceWithPayloads.transliteration_from_sample()
        
        response = user_client_with_expired_api_key.post(endpoint, json=payload)
        
        assert response.status_code in [401, 403], (
            f"Expected 401/403, got {response.status_code}. Response: {response.text}"
        )
        
        data = response.json()
        assert "detail" in data
        
        print(f"\n✅ USER Transliteration correctly blocked with invalid key")
        print(f"   Error: {data['detail']}")

    def test_text_language_detection_services_with_invalid_api_key_User(self, user_client_with_expired_api_key):
        """
        User : Test Text Language Detection service with invalid API key
        """
        endpoint = "/api/v1/language-detection/inference"
        payload = ServiceWithPayloads.text_language_detection_from_sample()
        
        response = user_client_with_expired_api_key.post(endpoint, json=payload)
        
        assert response.status_code in [401, 403], (
            f"Expected 401/403, got {response.status_code}. Response: {response.text}"
        )
        
        data = response.json()
        assert "detail" in data
        
        print(f"\n✅ USER Text Language Detection correctly blocked with invalid key")
        print(f"   Error: {data['detail']}")

    def test_speaker_diarization_services_with_invalid_api_key_User(self, user_client_with_expired_api_key):
        """
        User : Test Speaker Diarization service with invalid API key
        """
        endpoint = "/api/v1/speaker-diarization/inference"
        payload = ServiceWithPayloads.speaker_diarization_from_sample()
        
        response = user_client_with_expired_api_key.post(endpoint, json=payload)
        
        assert response.status_code in [401, 403], (
            f"Expected 401/403, got {response.status_code}. Response: {response.text}"
        )
        
        data = response.json()
        assert "detail" in data
        
        print(f"\n✅ USER Speaker Diarization correctly blocked with invalid key")
        print(f"   Error: {data['detail']}")

    def test_language_diarization_services_with_invalid_api_key_User(self, user_client_with_expired_api_key):
        """
        User : Test Language Diarization service with invalid API key
        """
        endpoint = "/api/v1/language-diarization/inference"
        payload = ServiceWithPayloads.language_diarization_from_sample()
        
        response = user_client_with_expired_api_key.post(endpoint, json=payload)
        
        assert response.status_code in [401, 403], (
            f"Expected 401/403, got {response.status_code}. Response: {response.text}"
        )
        
        data = response.json()
        assert "detail" in data
        
        print(f"\n✅ USER Language Diarization correctly blocked with invalid key")
        print(f"   Error: {data['detail']}")

    def test_audio_language_detection_services_with_invalid_api_key_User(self, user_client_with_expired_api_key):
        """
        User : Test Audio Language Detection service with invalid API key
        """
        endpoint = "/api/v1/audio-lang-detection/inference"
        payload = ServiceWithPayloads.audio_language_detection_from_sample()
        
        response = user_client_with_expired_api_key.post(endpoint, json=payload)
        
        assert response.status_code in [401, 403], (
            f"Expected 401/403, got {response.status_code}. Response: {response.text}"
        )
        
        data = response.json()
        assert "detail" in data
        
        print(f"\n✅ USER Audio Language Detection correctly blocked with invalid key")
        print(f"   Error: {data['detail']}")

    def test_ner_services_with_invalid_api_key_User(self, user_client_with_expired_api_key):
        """
        User : Test NER service with invalid API key
        """
        endpoint = "/api/v1/ner/inference"
        payload = ServiceWithPayloads.ner_from_sample()
        
        response = user_client_with_expired_api_key.post(endpoint, json=payload)
        
        assert response.status_code in [401, 403], (
            f"Expected 401/403, got {response.status_code}. Response: {response.text}"
        )
        
        data = response.json()
        assert "detail" in data
        
        print(f"\n✅ USER NER correctly blocked with invalid key")
        print(f"   Error: {data['detail']}")

    def test_ocr_services_with_invalid_api_key_User(self, user_client_with_expired_api_key):
        """
        User : Test OCR service with invalid API key
        """
        endpoint = "/api/v1/ocr/inference"
        payload = ServiceWithPayloads.ocr_from_sample()
        
        response = user_client_with_expired_api_key.post(endpoint, json=payload)
        
        assert response.status_code in [401, 403], (
            f"Expected 401/403, got {response.status_code}. Response: {response.text}"
        )
        
        data = response.json()
        assert "detail" in data
        
        print(f"\n✅ USER OCR correctly blocked with invalid key")
        print(f"   Error: {data['detail']}")

    def test_pipeline_services_with_invalid_api_key_User(self, user_client_with_expired_api_key):
        """
        User : Test Pipeline service with invalid API key
        """
        endpoint = "/api/v1/pipeline/inference"
        payload = ServiceWithPayloads.pipeline_from_sample()
        
        response = user_client_with_expired_api_key.post(endpoint, json=payload)
        
        assert response.status_code in [401, 403], (
            f"Expected 401/403, got {response.status_code}. Response: {response.text}"
        )
        
        data = response.json()
        assert "detail" in data
        
        print(f"\n✅ USER Pipeline correctly blocked with invalid key")
        print(f"   Error: {data['detail']}")


class TestUserServicesWithNoAPIKey:
    """Test USER role access to AI services with NO API key"""
    
    def test_nmt_services_with_no_api_key_User(self, user_client_with_no_api_key):
        """
        User : Test NMT service with no API key
        """
        endpoint = "/api/v1/nmt/inference"
        payload = ServiceWithPayloads.nmt_from_sample()
        
        response = user_client_with_no_api_key.post(endpoint, json=payload)
        
        assert response.status_code in [401, 403], (
            f"Expected 401/403, got {response.status_code}. Response: {response.text}"
        )
        
        data = response.json()
        assert "detail" in data
        
        print(f"\n✅ USER NMT correctly blocked with no API key")
        print(f"   Error: {data['detail']['message']}, {data['detail']}")

    def test_asr_service_with_no_api_key_User(self, user_client_with_no_api_key):
        """
        User : Test ASR service with no API key
        """
        endpoint = "/api/v1/asr/inference"
        payload = ServiceWithPayloads.asr_from_sample()
        
        response = user_client_with_no_api_key.post(endpoint, json=payload)
        
        assert response.status_code in [401, 403], (
            f"Expected 401/403, got {response.status_code}. Response: {response.text}"
        )
        
        data = response.json()
        assert "detail" in data
        
        print(f"\n✅ USER ASR correctly blocked with no API key")
        #print(f"   Error: {data['detail']['message']}, {data['detail']['code']}")
        print(f"   Error: {data['detail']}")
        print(f"   Error: {data['detail']}")

    def test_tts_service_with_no_api_key_User(self, user_client_with_no_api_key):
        """
        User : Test TTS service with no API key
        """
        endpoint = "/api/v1/tts/inference"
        payload = ServiceWithPayloads.tts_from_sample()
        
        response = user_client_with_no_api_key.post(endpoint, json=payload)
        
        assert response.status_code in [401, 403], (
            f"Expected 401/403, got {response.status_code}. Response: {response.text}"
        )
        
        data = response.json()
        assert "detail" in data
        
        print(f"\n✅ USER TTS correctly blocked with no API key")
        print(f"   Error: {data['detail']['message']}, {data['detail']}")

    def test_transliteration_service_with_no_api_key_User(self, user_client_with_no_api_key):
        """
        User : Test Transliteration service with no API key
        """
        endpoint = "/api/v1/transliteration/inference"
        payload = ServiceWithPayloads.transliteration_from_sample()
        
        response = user_client_with_no_api_key.post(endpoint, json=payload)
        
        assert response.status_code in [401, 403], (
            f"Expected 401/403, got {response.status_code}. Response: {response.text}"
        )
        
        data = response.json()
        assert "detail" in data
        
        print(f"\n✅ USER Transliteration correctly blocked with no API key")
        print(f"   Error: {data['detail']['message']}, {data['detail']}")

    def test_text_language_detection_services_with_no_api_key_User(self, user_client_with_no_api_key):
        """
        User : Test Text Language Detection service with no API key
        """
        endpoint = "/api/v1/language-detection/inference"
        payload = ServiceWithPayloads.text_language_detection_from_sample()
        
        response = user_client_with_no_api_key.post(endpoint, json=payload)
        
        assert response.status_code in [401, 403], (
            f"Expected 401/403, got {response.status_code}. Response: {response.text}"
        )
        
        data = response.json()
        assert "detail" in data
        
        print(f"\n✅ USER Text Language Detection correctly blocked with no API key")
        print(f"   Error: {data['detail']['message']}, {data['detail']}")

    def test_speaker_diarization_services_with_no_api_key_User(self, user_client_with_no_api_key):
        """
        User : Test Speaker Diarization service with no API key
        """
        endpoint = "/api/v1/speaker-diarization/inference"
        payload = ServiceWithPayloads.speaker_diarization_from_sample()
        
        response = user_client_with_no_api_key.post(endpoint, json=payload)
        
        assert response.status_code in [401, 403], (
            f"Expected 401/403, got {response.status_code}. Response: {response.text}"
        )
        
        data = response.json()
        assert "detail" in data
        
        print(f"\n✅ USER Speaker Diarization correctly blocked with no API key")
        print(f"   Error: {data['detail']['message']}, {data['detail']}")

    def test_language_diarization_services_with_no_api_key_User(self, user_client_with_no_api_key):
        """
        User : Test Language Diarization service with no API key
        """
        endpoint = "/api/v1/language-diarization/inference"
        payload = ServiceWithPayloads.language_diarization_from_sample()
        
        response = user_client_with_no_api_key.post(endpoint, json=payload)
        
        assert response.status_code in [401, 403], (
            f"Expected 401/403, got {response.status_code}. Response: {response.text}"
        )
        
        data = response.json()
        assert "detail" in data
        
        print(f"\n✅ USER Language Diarization correctly blocked with no API key")
        print(f"   Error: {data['detail']['message']}, {data['detail']}")

    def test_audio_language_detection_services_with_no_api_key_User(self, user_client_with_no_api_key):
        """
        User : Test Audio Language Detection service with no API key
        """
        endpoint = "/api/v1/audio-lang-detection/inference"
        payload = ServiceWithPayloads.audio_language_detection_from_sample()
        
        response = user_client_with_no_api_key.post(endpoint, json=payload)
        
        assert response.status_code in [401, 403], (
            f"Expected 401/403, got {response.status_code}. Response: {response.text}"
        )
        
        data = response.json()
        assert "detail" in data
        
        print(f"\n✅ USER Audio Language Detection correctly blocked with no API key")
        print(f"   Error: {data['detail']['message']}, {data['detail']}")

    def test_ner_services_with_no_api_key_User(self, user_client_with_no_api_key):
        """
        User : Test NER service with no API key
        """
        endpoint = "/api/v1/ner/inference"
        payload = ServiceWithPayloads.ner_from_sample()
        
        response = user_client_with_no_api_key.post(endpoint, json=payload)
        
        assert response.status_code in [401, 403], (
            f"Expected 401/403, got {response.status_code}. Response: {response.text}"
        )
        
        data = response.json()
        assert "detail" in data
        
        print(f"\n✅ USER NER correctly blocked with no API key")
        print(f"   Error: {data['detail']['message']}, {data['detail']}")

    def test_ocr_services_with_no_api_key_User(self, user_client_with_no_api_key):
        """
        User : Test OCR service with no API key
        """
        endpoint = "/api/v1/ocr/inference"
        payload = ServiceWithPayloads.ocr_from_sample()
        
        response = user_client_with_no_api_key.post(endpoint, json=payload)
        
        assert response.status_code in [401, 403], (
            f"Expected 401/403, got {response.status_code}. Response: {response.text}"
        )
        
        data = response.json()
        assert "detail" in data
        
        print(f"\n✅ USER OCR correctly blocked with no API key")
        print(f"   Error: {data['detail']['message']}, {data['detail']['error']}")
        #print(data)

    def test_pipeline_services_with_no_api_key_User(self, user_client_with_no_api_key):
        """
        User : Test Pipeline service with no API key
        """
        endpoint = "/api/v1/pipeline/inference"
        payload = ServiceWithPayloads.pipeline_from_sample()
        
        response = user_client_with_no_api_key.post(endpoint, json=payload)
        
        assert response.status_code in [401, 403], (
            f"Expected 401/403, got {response.status_code}. Response: {response.text}"
        )
        
        data = response.json()
        assert "detail" in data
        
        print(f"\n✅ USER Pipeline correctly blocked with no API key")
        #print(f"   Error: {data['detail']['message']}, {data['detail']['code']}")
        print(f"   Error: {data['detail']}")