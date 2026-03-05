import React, { useState, useEffect } from 'react';
import { Clock } from 'lucide-react';

interface TimerProps {
  startTime: number | string;
}

const Timer: React.FC<TimerProps> = ({ startTime }) => {
  const [elapsed, setElapsed] = useState<number>(0);

  useEffect(() => {
    // Normalize startTime: handle both ms timestamp and ISO date string
    let startMs: number;
    if (typeof startTime === 'string') {
      startMs = new Date(startTime).getTime();
    } else {
      startMs = startTime;
    }

    // Protect against invalid values
    if (isNaN(startMs) || startMs <= 0) {
      setElapsed(0);
      return;
    }

    const calcElapsed = () => {
      const diff = Date.now() - startMs;
      // Protect against negative values (clock skew or future timestamps)
      return Math.max(0, diff);
    };

    setElapsed(calcElapsed());

    const interval = setInterval(() => {
      setElapsed(calcElapsed());
    }, 1000);

    return () => clearInterval(interval);
  }, [startTime]);

  const formatTime = (ms: number) => {
    const totalSeconds = Math.floor(ms / 1000);
    const minutes = Math.floor(totalSeconds / 60);
    const seconds = totalSeconds % 60;

    // Cap at 99:59 for readability
    if (minutes >= 100) {
      return '99:59+';
    }

    return `${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
  };

  // Alert colors based on wait time
  const getTimerColor = (ms: number) => {
    const minutes = ms / 1000 / 60;
    if (minutes >= 100) return 'text-red-400';
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