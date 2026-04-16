export function SegmentTable({ segments, names, onNameChange }) {
  if (!segments?.length) {
    return <p>No segments yet.</p>;
  }

  return (
    <table className="segments-table">
      <thead>
        <tr>
          <th>#</th>
          <th>Start</th>
          <th>End</th>
          <th>Name</th>
          <th>Strategy</th>
        </tr>
      </thead>
      <tbody>
        {segments.map((segment, idx) => (
          <tr key={`${segment.index}-${segment.startSec}`}>
            <td>{segment.index + 1}</td>
            <td>{formatSeconds(segment.startSec)}</td>
            <td>{segment.endSec == null ? "END" : formatSeconds(segment.endSec)}</td>
            <td>
              <input value={names[idx] ?? segment.name} onChange={(event) => onNameChange(idx, event.target.value)} />
            </td>
            <td>{segment.strategy}</td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}

function formatSeconds(total) {
  const h = Math.floor(total / 3600);
  const m = Math.floor((total % 3600) / 60);
  const s = total % 60;
  const mm = `${m}`.padStart(2, "0");
  const ss = `${s}`.padStart(2, "0");
  return h > 0 ? `${h}:${mm}:${ss}` : `${mm}:${ss}`;
}
