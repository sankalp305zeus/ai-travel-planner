export default function ShinyText({ text, className }) {
  return <span className={`text-[#F0EDE8] drop-shadow-md ${className || ''}`}>{text}</span>
}
