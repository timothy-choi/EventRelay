import Link from "next/link";

const links = [
  { href: "/", label: "Dashboard" },
  { href: "/endpoints", label: "Endpoints" },
  { href: "/deliveries", label: "Deliveries" },
  { href: "/test-webhooks", label: "Test Webhooks" },
];

export function Nav() {
  return (
    <nav className="nav">
      <div className="brand">EventRelay</div>
      <div className="nav-links">
        {links.map((link) => (
          <Link key={link.href} href={link.href}>
            {link.label}
          </Link>
        ))}
      </div>
    </nav>
  );
}
