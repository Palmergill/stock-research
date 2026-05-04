import { useState, FormEvent } from 'react';

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
    <form onSubmit={handleSubmit} className="search-form">
      <input
        type="text"
        value={ticker}
        onChange={(e) => setTicker(e.target.value)}
        placeholder="Enter ticker (e.g., AAPL)"
        className="search-input"
        disabled={loading}
        autoFocus
      />
      <button type="submit" className="search-button" disabled={loading}>
        {loading ? 'Loading...' : 'Search'}
      </button>
    </form>
  );
};
