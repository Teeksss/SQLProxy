import React from 'react';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { vscDarkPlus } from 'react-syntax-highlighter/dist/esm/styles/prism';
import { Copy } from 'lucide-react';
import { useToast } from '@/components/ui/use-toast';
import { Button } from '@/components/ui/button';

/**
 * SQL syntax highlighting component that displays SQL code with proper formatting
 * 
 * @param {Object} props Component props
 * @param {string} props.code SQL code to highlight
 * @param {boolean} props.showLineNumbers Whether to show line numbers
 * @param {number} props.maxHeight Maximum height of the code block (with scrolling)
 * @param {boolean} props.showCopyButton Whether to show the copy button
 * @returns {JSX.Element} Highlighted SQL code component
 */
const SQLHighlight = ({ 
  code, 
  showLineNumbers = false, 
  maxHeight = null,
  showCopyButton = true
}) => {
  const { toast } = useToast();
  
  // Format the SQL code for better display
  const formatSql = (sqlString) => {
    if (!sqlString || typeof sqlString !== 'string') {
      return '';
    }
    return sqlString.trim();
  };
  
  const formattedCode = formatSql(code);
  
  // Copy code to clipboard
  const handleCopy = () => {
    navigator.clipboard.writeText(formattedCode);
    toast({
      title: 'Kopyalandı',
      description: 'SQL sorgusu panoya kopyalandı',
      duration: 2000,
    });
  };
  
  return (
    <div className="relative rounded-md overflow-hidden" style={{ maxHeight: maxHeight }}>
      <SyntaxHighlighter
        language="sql"
        style={vscDarkPlus}
        showLineNumbers={showLineNumbers}
        customStyle={{
          margin: 0,
          borderRadius: '0.375rem',
          fontSize: '0.875rem',
          overflow: maxHeight ? 'auto' : 'visible',
          maxHeight: maxHeight,
        }}
      >
        {formattedCode}
      </SyntaxHighlighter>
      
      {showCopyButton && formattedCode && (
        <Button 
          variant="ghost" 
          size="icon" 
          className="absolute top-2 right-2 h-8 w-8 bg-gray-800 bg-opacity-80 hover:bg-gray-700"
          onClick={handleCopy}
          title="Kopyala"
        >
          <Copy className="h-4 w-4 text-gray-100" />
        </Button>
      )}
    </div>
  );
};

// Son güncelleme: 2025-05-20 05:58:23
// Güncelleyen: Teeksss

export default SQLHighlight;