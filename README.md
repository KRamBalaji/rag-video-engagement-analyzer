# RAG Video Analyzer

A full-stack application that analyzes video content from YouTube and Instagram using Retrieval-Augmented Generation (RAG) technology. Extract transcripts, chunk video content, store embeddings in a vector database, and chat with AI to get insights from your videos with source citations.

## Features

- **Multi-Platform Support**: Extract and analyze content from YouTube and Instagram videos
- **Automatic Transcript Extraction**: Retrieves transcripts from YouTube videos
- **RAG Pipeline**: Chunks video transcripts and stores embeddings in Chroma vector database
- **AI-Powered Chat**: Ask questions about video content and get answers with source citations
- **Citation Tracking**: Get references to the exact timestamps and quotes from source videos
- **Real-time Processing**: Streaming responses for chat interactions
- **Cross-Origin Support**: CORS-enabled API for seamless frontend-backend communication

## Tech Stack

### Backend
- **Framework**: FastAPI (Python)
- **Vector Database**: Chroma DB
- **Embeddings**: LangChain + Hugging Face Sentence Transformers
- **LLM**: Groq API (Llama 3.1)
- **Video Services**: YouTube DL, YouTube API
- **Libraries**: Pydantic, LangChain, Python-dotenv

### Frontend
- **Framework**: Next.js 16 (React 19)
- **Styling**: Tailwind CSS
- **Type Safety**: TypeScript
- **Package Manager**: npm

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         FRONTEND (Next.js)                      │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │              React Chat Interface                        │   │
│  │  - Video URL Input                                       │   │
│  │  - Chat Messages                                         │   │
│  │  - Citation Display                                      │   │
│  └──────────────────────────────────────────────────────────┘   │
└──────────────────────────┬──────────────────────────────────────┘
                           │ HTTP / JSON
                           ▼
┌──────────────────────────────────────────────────────────────────┐
│                  BACKEND API (FastAPI)                           │
│                                                                  │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │              API Endpoints                                 │  │
│  │  - /api/process_videos    (Video ingestion)                │  │
│  │  - /api/chat              (RAG queries)                    │  │
│  │  - /health                (Health check)                   │  │
│  │  - /proxy-thumbnail       (Image proxy)                    │  │
│  └────────────────────────────────────────────────────────────┘  │
│                           │                                      │
│        ┌──────────────────┼──────────────────┐                   │
│        ▼                  ▼                   ▼                  │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────────┐          │
│  │   Services   │ │     RAG      │ │  LLM Integration │          │
│  │              │ │   Pipeline   │ │                  │          │
│  │ • YouTube    │ │              │ │  • Groq API      │          │
│  │ • Instagram  │ │ • Chunking   │ │  • Llama 3.1     │          │
│  │ • Transcript │ │ • Embedding  │ │                  │          │
│  │              │ │ • Retrieval  │ │                  │          │
│  └──────────────┘ └──────────────┘ └──────────────────┘          │
│        │                  │                                      │
│        └──────────────────┼───────────────────────────────┐      │
│                           ▼                               │      │
│  ┌──────────────────────────────────────────────┐         │      │
│  │      Chroma Vector Database                  │         │      │
│  │                                              │         │      │
│  │  • Stores chunk embeddings                   │         │      │
│  │  • Maintains metadata (timestamp, source)    │         │      │
│  │  • Enables similarity search                 │         │      │
│  └──────────────────────────────────────────────┘         │      │
│                                                           │      │
│  ┌──────────────────────────────────────────────┐         │      │
│  │      External APIs                           │◄────────┘      │
│  │                                              │                │
│  │  • YouTube API / yt-dlp                      │                │
│  │  • Instagram API                             │                │
│  │  • Hugging Face (Embeddings)                 │                │
│  │  • Groq API (LLM)                            │                │
│  └──────────────────────────────────────────────┘                │
└──────────────────────────────────────────────────────────────────┘
```

### Data Flow Diagram

```
Video URL Input
     │
     ▼
┌─────────────────────────────────────┐
│  Extract Video Metadata             │
│  (Title, Duration, Description)     │
└──────────────┬──────────────────────┘
               │
               ▼
    ┌──────────────────────┐
    │ Extract Transcript   │
    │ (YouTube/Instagram)  │
    └──────────┬───────────┘
               │
               ▼
    ┌──────────────────────┐
    │ Split into Chunks    │
    │ (Sliding window)     │
    └──────────┬───────────┘
               │
               ▼
    ┌──────────────────────┐
    │ Generate Embeddings  │
    │ (Sentence Transformer)
    └──────────┬───────────┘
               │
               ▼
    ┌──────────────────────┐
    │ Store in Chroma DB   │
    │ (with metadata)      │
    └──────────┬───────────┘
               │
               ▼
         ✓ Ready for Chat

User Question
     │
     ▼
┌─────────────────────────────────────┐
│  Convert to Embedding               │
└──────────────┬──────────────────────┘
               │
               ▼
    ┌──────────────────────┐
    │ Vector Search        │
    │ (Find similar chunks)│
    └──────────┬───────────┘
               │
               ▼
    ┌──────────────────────┐
    │ Build Context        │
    │ + Citations          │
    └──────────┬───────────┘
               │
               ▼
    ┌──────────────────────┐
    │ Query Groq LLM       │
    │ + Context            │
    └──────────┬───────────┘
               │
               ▼
    ┌──────────────────────┐
    │ Generate Answer      │
    │ + Extract Citations  │
    └──────────┬───────────┘
               │
               ▼
         Return to Frontend
```

## Project Structure

```
rag-video-analyzer/
├── backend/
│   ├── app/
│   │   ├── main.py                 # FastAPI application and endpoints
│   │   ├── services/
│   │   │   ├── youtube_service.py  # YouTube video/transcript handling
│   │   │   ├── instagram_service.py # Instagram metadata extraction
│   │   │   └── transcript_service.py # Transcript processing
│   │   └── rag/
│   │       ├── chunking.py         # Text chunking logic
│   │       └── vector_store.py     # Chroma vector database operations
│   ├── chroma_db/                  # Vector database storage
│   ├── requirements.txt            # Python dependencies
│   └── .venv/                      # Python virtual environment
├── frontend/
│   ├── src/
│   │   └── app/
│   │       ├── page.tsx            # Main chat interface
│   │       ├── layout.tsx          # App layout
│   │       └── globals.css         # Global styles
│   ├── package.json                # Node dependencies
│   ├── tsconfig.json               # TypeScript config
│   ├── next.config.ts              # Next.js config
│   └── tailwind.config.js          # Tailwind CSS config
└── README.md                       # This file
```

## Installation

### Prerequisites
- Python 3.9+
- Node.js 18+
- npm or yarn
- Groq API key (get one at [groq.com](https://groq.com))

### Backend Setup

1. Navigate to the backend directory:
```bash
cd backend
```

2. Create and activate a virtual environment:
```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Create a `.env` file in the backend directory with your API keys:
```env
GROQ_API_KEY=your_groq_api_key_here
GROQ_MODEL=llama-3.1-8b-instant
```

### Frontend Setup

1. Navigate to the frontend directory:
```bash
cd frontend
```

2. Install dependencies:
```bash
npm install
```

## Running the Application

### Start the Backend Server

From the `backend` directory:
```bash
uvicorn app.main:app --reload --port 8000
```

The API will be available at `http://localhost:8000`
- Health check: `http://localhost:8000/health`
- API docs: `http://localhost:8000/docs`

### Start the Frontend Development Server

From the `frontend` directory:
```bash
npm run dev
```

The application will be available at `http://localhost:3000`

## API Endpoints

### Health Check
- **GET** `/health` - Check API status

### Video Processing
- **POST** `/api/process_videos` - Process and analyze videos
  - **Request Body**:
    ```json
    {
      "video_urls": ["https://youtube.com/watch?v=..."],
      "session_id": "unique-session-id"
    }
    ```
  - **Response**: Video metadata and processing status

### Chat
- **POST** `/api/chat` - Chat with AI about video content
  - **Request Body**:
    ```json
    {
      "session_id": "unique-session-id",
      "message": "What is this video about?",
      "history": []
    }
    ```
  - **Response**:
    ```json
    {
      "answer": "AI response text...",
      "citations": [
        {
          "source": "video_title",
          "timestamp": "00:30:45",
          "quote": "Relevant excerpt..."
        }
      ]
    }
    ```

### Thumbnail Proxy
- **GET** `/proxy-thumbnail?url=...` - Proxy thumbnail images

## How It Works

### 1. Video Processing Pipeline
1. User submits video URL (YouTube or Instagram)
2. Extract video metadata (title, description, duration)
3. Download and extract transcript using yt-dlp
4. Split transcript into chunks using a sliding window algorithm
5. Generate embeddings for each chunk using Sentence Transformers
6. Store embeddings and metadata in Chroma vector database

### 2. Chat & RAG System
1. User asks a question about video content
2. Convert question to embedding
3. Retrieve relevant chunks from vector database (similarity search)
4. Create context from top-k relevant chunks with source citations
5. Send context + question to Groq LLM
6. LLM generates answer with reasoning
7. Extract citations from retrieved chunks
8. Return answer with source citations to frontend

### 3. Citation Tracking
- Each chunk maintains metadata: video title, timestamp range, original text
- Retrieved chunks are mapped to source citations
- Citations include video title, timestamp, and relevant quote

## Environment Variables

```env
# Backend
GROQ_API_KEY=sk_...              # Your Groq API key
GROQ_MODEL=llama-3.1-8b-instant  # LLM model to use

# Optional
YOUTUBE_API_KEY=...               # For enhanced YouTube metadata
```

## Usage Example

1. **Open the application** at `http://localhost:3000`
2. **Paste a video URL** (YouTube or Instagram)
3. **Wait for processing** - the system will extract and index the transcript
4. **Ask questions** in the chat interface
5. **Review citations** - see where in the video each answer comes from

## Development

### Backend Development
- Code is in `backend/app/`
- Main entry point: `backend/app/main.py`
- FastAPI will auto-reload on code changes with `--reload` flag

### Frontend Development
- Code is in `frontend/src/`
- Next.js will hot-reload on file changes
- Use `npm run lint` to check code quality

## Vector Database

The application uses **Chroma DB** for vector storage:
- Stores embeddings of video transcript chunks
- Enables fast similarity search for RAG retrieval
- Persisted storage in `backend/chroma_db/`
- Supports adding/removing videos dynamically

## Building for Production

### Backend
```bash
cd backend
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### Frontend
```bash
cd frontend
npm run build
npm start
```

## Troubleshooting

### Backend Issues
- **ModuleNotFoundError**: Ensure virtual environment is activated and dependencies are installed
- **GROQ_API_KEY not found**: Check `.env` file has correct key
- **Connection refused**: Ensure backend is running on port 8000

### Frontend Issues
- **Cannot find module**: Run `npm install` in frontend directory
- **Port 3000 already in use**: Change port with `npm run dev -- -p 3001`

### Video Processing Issues
- **Transcript extraction fails**: Some videos may have restricted transcripts
- **Instagram videos**: Requires metadata extraction only (no transcript)

## Limitations & trade-offs

- Instagram videos: Metadata extraction only (no transcript)
- Transcript availability: Not all YouTube videos have transcripts
- Rate limiting: Groq API has usage limits based on your plan
- Vector DB size: Large collections may impact search performance
- Some Instagram Reels don't expose full engagement metrics; shows N/A instead of guessing.
- Follower count is not always available; reported as "unknown" when missing.

## Future Enhancements

- Support for video subtitles (multiple languages)
- Document upload support (PDF, text files)
- Multi-session chat history persistence
- Advanced filtering and search options
- Batch video processing
- Video summary generation
- Export chat conversations


## Why this is high quality and low cost at 1000 creators/day
- One-time transcription & embedding per video; cached in Chroma.
- Open-source embeddings (BGE/E5) → near-zero marginal cost.
- Groq LLM → fast and cheaper than GPT-4 at scale.
- Chroma → simple, embedded vector store, scalable path to Qdrant/Pinecone later.
- Clear path to batching, async jobs, and multi-tenant isolation.

## Contributing

Contributions are welcome! Please feel free to submit pull requests or open issues.

## License

This project is open source and available under the MIT License.

## Support

For issues, questions, or suggestions, please open an issue in the repository.

---

**Last Updated**: June 2026