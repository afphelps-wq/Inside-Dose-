import { useParams } from 'react-router-dom'

export default function Drug() {
  const { rxcui } = useParams()
  return (
    <section>
      <h1>Drug {rxcui}</h1>
      <p>Drug details are coming soon.</p>
    </section>
  )
}
