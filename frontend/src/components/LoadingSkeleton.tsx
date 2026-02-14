import React from 'react';

export const LoadingSkeleton: React.FC = () => {
  return (
    <>
      {/* Metric Card Skeleton */}
      <div className="loading-skeleton">
        <div className="skeleton-title" />
        <div className="skeleton-line" style={{ width: '30%' }} />
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '16px', marginTop: '20px' }}>
          <div>
            <div className="skeleton-line short" />
            <div className="skeleton-line" style={{ width: '60%' }} />
          </div>
          <div>
            <div className="skeleton-line short" />
            <div className="skeleton-line" style={{ width: '60%' }} />
          </div>
          <div>
            <div className="skeleton-line short" />
            <div className="skeleton-line" style={{ width: '60%' }} />
          </div>
        </div>
      </div>

      {/* Chart Skeletons */}
      {[1, 2, 3, 4].map((i) => (
        <div key={i} className="loading-skeleton">
          <div className="skeleton-title" style={{ width: '40%' }} />
          <div className="skeleton-line" style={{ height: '200px', marginTop: '20px' }} />
        </div>
      ))}
    </>
  );
};
