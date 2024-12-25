# Jukebox of Musical Ideas

This is a service that generates wav files from chord progressions using the [musicpy](https://github.com/c-bata/musicpy) library.

## Usage

To use the service, you can send a POST request to the `/generate` endpoint with a JSON body containing the chord progression.

```bash
curl -X POST -H "Content-Type: application/json" -d '{"key": "C", "progression": ["C", "G", "A", "F"], "tempo": 120}' http://localhost:8000/generate/
```

The response will be a wav file.

## Development

To run the service, you can use the following command:

```bash
poetry run uvicorn jukebox_of_musical_ideas.main:app --reload
```
