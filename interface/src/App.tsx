import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { MainLayout } from '@/components/layout/MainLayout';
import VideoPlayerPage from '@/pages/VideoPlayerPage';
import SubmissionsPage from '@/pages/SubmissionsPage';
import './App.css';

function App() {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<MainLayout />} />
        <Route path="/video-player" element={<VideoPlayerPage />} />
        <Route path="/submissions" element={<SubmissionsPage />} />
      </Routes>
    </Router>
  );
}

export default App;
