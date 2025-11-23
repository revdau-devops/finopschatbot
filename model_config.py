def model_config(model: str):
    if model == "llama":
        return {
            "api_host": "http://127.0.0.1:11434/api/chat",
            "api_key": None,
            "model": "llama3:70b-instruct",
        }
    if model == "groq":
        return {
            "api_host": "https://api.groq.com/openai/v1/chat/completions",
            "api_key": "gAAAAABpI08rB381B53XHVdkKK2_wez1XOiuYJClFNSUM2HPC6sv6iTwxOShZ7twXAyNiAebwfuAQXU845dyWbEEeRe6L15-wIJzJhuQO07pq1NOd2gMj1luc1nIi45I7RIXco_kviuEPu7geCHCKnoBAq_oizgFcg==",
            "model": "llama-3.1-8b-instant",
        }
