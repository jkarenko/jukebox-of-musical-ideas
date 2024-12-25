from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
import tempfile
import os
from musicpy.algorithms import C, drum, P
from musicpy.daw import daw
from .song import Song
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

@app.post("/generate/")
async def generate_progression(prog: Song):
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
        
        # Create a piece with two tracks if drums are enabled
        tracks = [progression]
        instruments = ["Acoustic Grand Piano"]
        channels = [0]
        
        if prog.drums:
            drum_obj = drum("K;H,H,S;H,H") 
            drum_pattern = drum_obj.notes * len(chords)
            tracks.append(drum_pattern)
            instruments.append("Synth Drum")
            channels.append(9)  # Channel 9 is reserved for drums in MIDI
            
        piece = P(
            tracks=tracks,
            instruments=instruments,
            bpm=prog.tempo,
            channels=channels
        )
        
        # Create temporary file for WAV
        temp_dir = tempfile.mkdtemp()
        output_path = os.path.join(temp_dir, "progression.wav")
        logger.info(f"Will save to: {output_path}")
        
        # Initialize DAW and export
        logger.info(f"Initializing DAW with tempo: {prog.tempo}")
        my_daw = daw(len(tracks))
        
        # Load sf2 file for all channels
        logger.info("Loading sf2 file")
        for i in range(len(tracks)):
            my_daw.load(i, "./soundfonts/arachno.sf2")
        
        # Export to WAV
        logger.info("Exporting piece to WAV")
        my_daw.export(
            piece,
            mode="wav",
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
