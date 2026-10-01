function LoadingState({ message = 'Loading project data…' }) {
  return (
    <div className="loading-shell">
      <div className="spinner" aria-hidden="true" />
      <div>{message}</div>
    </div>
  );
}

export default LoadingState;
