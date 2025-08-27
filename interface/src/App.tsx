import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { MainLayout } from '@/components/layout/MainLayout';
import VideoPlayerPage from '@/pages/VideoPlayerPage';
import './App.css';

function App() {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<MainLayout />} />
        <Route path="/video-player" element={<VideoPlayerPage />} />
      </Routes>
    </Router>
  );
}

export default App;
