export default function Icon({ name, size = 19 }) {
  const paths = {
    grid: (
      <>
        <rect x="3" y="3" width="7" height="7" rx="1" />
        <rect x="14" y="3" width="7" height="7" rx="1" />
        <rect x="3" y="14" width="7" height="7" rx="1" />
        <rect x="14" y="14" width="7" height="7" rx="1" />
      </>
    ),
    bolt: <path d="m13 2-9 12h7l-1 8 10-13h-7z" />,
    chart: (
      <>
        <path d="M4 3v17h17" />
        <path d="m7 14 4-5 4 3 5-7" />
      </>
    ),
    funnel: <path d="M3 4h18l-7 8v7l-4 2v-9z" />,
    arrow: <path d="M4 12h16M14 6l6 6-6 6" />,
    clock: (
      <>
        <circle cx="12" cy="12" r="9" />
        <path d="M12 7v5l3 2" />
      </>
    ),
    check: <path d="m5 12 4 4L19 6" />,
    phone: (
      <path d="M8 3H4v4c0 7 6 13 13 13h4v-4l-5-2-2 2a12 12 0 0 1-6-6l2-2z" />
    ),
    search: (
      <>
        <circle cx="10" cy="10" r="6" />
        <path d="m15 15 5 5" />
      </>
    ),
    book: (
      <path d="M12 5C8 2 4 3 2 4v15c4-2 7-1 10 1 3-2 6-3 10-1V4c-3-1-6-2-10 1zM12 5v15" />
    ),
    target: (
      <>
        <circle cx="12" cy="12" r="9" />
        <circle cx="12" cy="12" r="5" />
        <circle cx="12" cy="12" r="1" />
      </>
    ),
    users: (
      <>
        <circle cx="9" cy="8" r="3" />
        <path d="M3 20v-2a6 6 0 0 1 12 0v2M17 5a3 3 0 0 1 0 6M18 14a5 5 0 0 1 3 6" />
      </>
    ),
    mail: (
      <>
        <rect x="3" y="5" width="18" height="14" rx="2" />
        <path d="m3 6 9 7 9-7" />
      </>
    ),
    info: (
      <>
        <circle cx="12" cy="12" r="9" />
        <path d="M12 10v7M12 6v1" />
      </>
    ),
    close: <path d="m6 6 12 12M18 6 6 18" />,
    download: <path d="M12 3v12m-5-5 5 5 5-5M4 17v4h16v-4" />,
    calendar: (
      <>
        <rect x="3" y="5" width="18" height="16" rx="2" />
        <path d="M7 2v6M17 2v6M3 11h18" />
      </>
    ),
    trophy: (
      <path d="M8 3h8v5a4 4 0 0 1-8 0zM8 5H3v2a5 5 0 0 0 6 5M16 5h5v2a5 5 0 0 1-6 5M12 12v7M7 21h10" />
    ),
  };
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.6"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
    >
      {paths[name] || paths.target}
    </svg>
  );
}
