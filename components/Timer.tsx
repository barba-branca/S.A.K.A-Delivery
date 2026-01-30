import React, { useState, useEffect } from 'react';
import { Clock } from 'lucide-react';

interface TimerProps {
  startTime: number;
}

const Timer: React.FC<TimerProps> = ({ startTime }) => {
  const [elapsed, setElapsed] = useState<number>(0);

  useEffect(() => {
    // Calculate initial immediately
    setElapsed(Date.now() - startTime);

    const interval = setInterval(() => {
      setElapsed(Date.now() - startTime);
    }, 1000);

    return () => clearInterval(interval);
  }, [startTime]);

  const formatTime = (ms: number) => {
    const totalSeconds = Math.floor(ms / 1000);
    const minutes = Math.floor(totalSeconds / 60);
    const seconds = totalSeconds % 60;
    
    // Formatting: MM:SS
    return `${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
  };

  // Alert colors based on wait time
  const getTimerColor = (ms: number) => {
    const minutes = ms / 1000 / 60;
    if (minutes > 30) return 'text-red-400';
    if (minutes > 15) return 'text-yellow-400';
    return 'text-slate-300';
  };

  return (
    <div className={`flex items-center gap-1 font-mono font-bold ${getTimerColor(elapsed)}`}>
      <Clock size={14} />
      <span>{formatTime(elapsed)}</span>
    </div>
  );
};

export default Timer;