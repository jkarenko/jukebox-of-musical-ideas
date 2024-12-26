from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
import tempfile
import os
from musicpy.algorithms import C, drum, P, translate
from musicpy.daw import daw
from .song import Song
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

# Example dictionary of typical drum beats

TYPICAL_DRUM_BEATS = {
    # "basic_rock": Kick+Hi-Hat on 1, Hi-Hat on 2, Snare+Hi-Hat on 3, Hi-Hat on 4
    "basic": "K;H,H,S;H,H",

    # "four_on_the_floor": Kick+Hi-Hat every beat
    "four_on_the_floor": "K;H,K;H,K;H,K;H",

    # Variation: "kick_snare_hat": Kick on 1, Hat on 2, Snare on 3, Hat on 4
    "kick_snare_hat": "K,H,S,H",

    # Syncopated: 
    #   1) Kick+Hi-Hat
    #   2) Hi-Hat
    #   3) Snare+Hi-Hat
    #   4) Half-beat rest: 0[l:1/2], then half-beat Kick: K[l:1/2]
    "syncopated": "K;H,H,S;H,0[l:1/2],K[l:1/2]",

    # "shuffle": Kick+Hi-Hat on 1, Hi-Hat on 2&, Snare+Hi-Hat on 3, Hi-Hat on 4&
    "shuffle": "K;H,0,H,S;H,0,H",
    
    # "half_time": Kick on 1, Hi-Hat on all beats, Snare on 3
    "half_time": "K;H,H,S;H,H",
    
    # "disco": Kick on 1&3, Hi-Hat on all beats, Snare on 2&4
    "disco": "K;H,S;H,K;H,S;H",
    
    # "waltz": 3/4 time - Kick on 1, Snare on 2&3, Hi-Hat throughout
    "waltz": "K;H,S;H,S;H",
    
    # "funk": Classic JB-style funk - syncopated kicks, snare on 2&4, steady hi-hat
    "funk": "K;H,H,K;H,S;H,K,H,S;H,K,H",
    
    # "breakbeat": Classic break pattern
    "breakbeat": "K;H,0,H,S;H,K,H,K;H,0,H,S;H,0,H",
    
    # "latin": Basic bossa nova inspired pattern
    "latin": "K;H,0,H,S;H,K,H",

    # "skank": Fast alternating bass and snare with constant hi-hat (punk/metal staple)
    "skank": "K;H,S;H,K;H,S;H",
    
    # "traditional_blast": Traditional blast beat - alternating kick/snare with hi-hat on kicks
    "traditional_blast": "K;H,S,K;H,S,K;H,S,K;H,S,t:1/2",
    
    # "hammer_blast": Everything hits together - kick, snare, and hi-hat in unison
    "hammer_blast": "K;S;H,K;S;H,K;S;H,K;S;H,r:2,t:1/4",
    
    # "euro_blast": Kick and snare alternate with constant hi-hat (aka "Running" blast)
    "euro_blast": "K;H,S;H,K;H,S;H,t:1/2" * 2,
    
    # "bomb_blast": Double-time with kick and cymbal together, snare offbeats
    "bomb_blast": "K;H,S,K;H,S,K;H,S,K;H,S",
}

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
        
        # Create tracks for the guitars, bass, and drums
        tracks = [progression]
        instruments = ["Distortion Guitar"]
        channels = [0]
        
        # Add another guitar track
        tracks.append(progression)
        instruments.append("Overdriven Guitar")
        channels.append(1)
        
        # Add a bass track
        bass_notes = [str(c.notes[0]) + "[l:1/4; i:1/4]" for c in chords]
        bass_track = translate(", ".join(bass_notes))
        print(bass_track)
        bass_track = bass_track - 24
        bass_track = bass_track * prog.bars
        tracks.append(bass_track)
        instruments.append(34)
        channels.append(2)
        
        if isinstance(prog.drums, str) and prog.drums in TYPICAL_DRUM_BEATS:
            drum_string = TYPICAL_DRUM_BEATS[prog.drums]
            drum_obj = drum(drum_string)
            drum_pattern = drum_obj.notes * len(chords)
            tracks.append(drum_pattern)
            instruments.append(127)
            channels.append(9)
        
        piece = P(
            tracks=tracks,
            instruments=instruments,
            bpm=prog.tempo,
            channels=channels
        )
        
        # Pan Guitars to the left and right
        piece.add_pan(value=0, ind=0,start_time=0, mode="percentage")
        piece.add_pan(value=100, ind=1,start_time=0, mode="percentage")
        
        # Set volume for instruments
        piece.add_volume(value=40, ind=0,start_time=0, mode="percentage")
        piece.add_volume(value=40, ind=1,start_time=0, mode="percentage")
        piece.add_volume(value=100, ind=2,start_time=0, mode="percentage")
        
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
