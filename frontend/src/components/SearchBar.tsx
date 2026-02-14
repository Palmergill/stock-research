import React, { useState, FormEvent } from 'react';

interface SearchBarProps {
  onSearch: (ticker: string) => void;
  loading: boolean;
}

export const SearchBar: React.FC<SearchBarProps> = ({ onSearch, loading }) => {
  const [ticker, setTicker] = useState('');

  const handleSubmit = (e: FormEvent) => {
    e.preventDefault();
    if (ticker.trim()) {
      onSearch(ticker.trim().toUpperCase());
    }
  };

  return (
    <form onSubmit={handleSubmit} style={styles.form}>
      <input
        type="text"
        value={ticker}
        onChange={(e) => setTicker(e.target.value)}
        placeholder="Enter ticker (e.g., AAPL)"
        style={styles.input}
        disabled={loading}
      />
      <button type="submit" style={styles.button} disabled={loading}>
        {loading ? 'Loading...' : 'Search'}
      </button>
    </form>
  );
};

const styles: Record<string, React.CSSProperties> = {
  form: {
    display: 'flex',
    gap: '12px',
    maxWidth: '400px',
    width: '100%',
  },
  input: {
    flex: 1,
    padding: '12px 16px',
    fontSize: '16px',
    border: '1px solid #334155',
    borderRadius: '8px',
    background: '#1e293b',
    color: '#e2e8f0',
    outline: 'none',
  },
  button: {
    padding: '12px 24px',
    fontSize: '16px',
    fontWeight: 500,
    border: 'none',
    borderRadius: '8px',
    background: '#3b82f6',
    color: 'white',
    cursor: 'pointer',
  },
};
