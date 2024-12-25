from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
import tempfile
import os
from musicpy.algorithms import C
from musicpy.daw import daw
from .chordprogression import ChordProgression
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

@app.post("/generate/")
async def generate_progression(prog: ChordProgression):
    try:
        # Convert chord names to musicpy chord objects
        logger.info(f"Converting chords: {prog.progression}")
        chords = [C(f"{chord}") for chord in prog.progression]
        logger.info(f"Created chord objects: {chords}")
        
        # Combine chords using addition
        progression = chords[0]  # Start with first chord
        logger.info(f"Starting progression with: {chords[0]}")
        for chord in chords[1:]:
            progression += chord
            logger.info(f"Added chord: {chord}, progression now: {progression}")
        
        # Repeat for requested bars
        logger.info(f"Repeating for {prog.bars} bars")
        progression = progression * prog.bars
        
        # Create temporary file for WAV
        temp_dir = tempfile.mkdtemp()
        output_path = os.path.join(temp_dir, "progression.wav")
        logger.info(f"Will save to: {output_path}")
        
        # Initialize DAW and export
        logger.info(f"Initializing DAW with tempo: {prog.tempo}")
        song = daw(1)
        
        # Load sf2 file
        logger.info("Loading sf2 file")
        song.load(0, "./soundfonts/arachno.sf2")
        
        # Export to WAV (following documentation example)
        logger.info("Exporting progression to WAV")
        song.export(
            progression,
            mode='wav',
            filename=output_path,
            bpm=prog.tempo
        )
        logger.info("Export complete")
        
        # Return the file
        return FileResponse(
            output_path,
            media_type="audio/wav",
            filename="progression.wav"
        )
    
    except Exception as e:
        logger.error(f"Error generating progression: {str(e)}", exc_info=True)
        raise HTTPException(status_code=400, detail=str(e))
