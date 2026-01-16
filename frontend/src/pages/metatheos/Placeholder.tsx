interface PlaceholderProps {
  title: string;
  description?: string;
}

const Placeholder = ({ title, description }: PlaceholderProps) => {
  return (
    <div className="metatheos-placeholder metatheos-fade-in">
      <span className="metatheos-kicker">Layer</span>
      <h1>{title}</h1>
      {description ? <p>{description}</p> : null}
      <div className="metatheos-divider" />
      <p className="metatheos-muted">TODO: Connect {title.toLowerCase()} data.</p>
    </div>
  );
};

export default Placeholder;
