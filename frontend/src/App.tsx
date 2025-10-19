import { useState } from 'react';
import axios from 'axios';

type ConversionOption = {
  value: string;
  label: string;
};

const conversionOptions: ConversionOption[] = [
  { value: 'pdf-to-png', label: 'PDF para PNG' },
  { value: 'docx-to-txt', label: 'DOCX para TXT' },
  { value: 'img-to-text', label: 'Imagem para Texto (OCR)' },
];

function App() {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [selectedConversion, setSelectedConversion] = useState<string>(conversionOptions[0].value);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  const handleFileChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    setError(null); 
    const file = event.target.files?.[0];
    if (file) {
      setSelectedFile(file);
    }
  };

  const handleConversionChange = (event: React.ChangeEvent<HTMLSelectElement>) => {
    setSelectedConversion(event.target.value);
  };

  const handleSubmit = async () => {
    if (!selectedFile) {
      setError('Por favor, selecione um arquivo primeiro.');
      return;
    }

    setIsLoading(true);
    setError(null);

    const formData = new FormData();
    formData.append('file', selectedFile);
    formData.append('conversionType', selectedConversion);

    try {
      const response = await axios.post('http://localhost:5000/api/convert', formData, {
        responseType: 'blob',
      });

      const url = window.URL.createObjectURL(new Blob([response.data]));

      const link = document.createElement('a');
      link.href = url;

      
      const outputFilename = 'new-archive.bin'; 
      link.setAttribute('download', outputFilename);

      document.body.appendChild(link);

      link.click();

      link.parentNode?.removeChild(link);
      window.URL.revokeObjectURL(url);

    } catch (err) {
      console.error('Erro no envio:', err);
      setError('Ocorreu um erro ao converter o arquivo. O servidor está rodando?');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div>
      <h1>Convertify</h1>

      <input type="file" onChange={handleFileChange} />

      {selectedFile && (
        <div>
          <p>Arquivo selecionado: {selectedFile.name}</p>
          <select value={selectedConversion} onChange={handleConversionChange}>
            {conversionOptions.map((option) => (
              <option key={option.value} value={option.value}>
                {option.label}
              </option>
            ))}
          </select>

          <button onClick={handleSubmit} disabled={isLoading}>
            {isLoading ? 'Convertendo...' : 'Converter'}
          </button>
        </div>
      )}

      {error && <p style={{ color: 'red' }}>{error}</p>}
    </div>
  );
}

export default App;