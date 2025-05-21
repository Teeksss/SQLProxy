import React, { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription, CardFooter } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { BarChart2, CheckCircle, AlertTriangle, Info, Copy, ChevronDown, ChevronUp } from 'lucide-react';
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from '@/components/ui/tooltip';
import { useToast } from '@/components/ui/use-toast';
import SQLHighlight from '@/components/SQLHighlight';
import { Accordion, AccordionContent, AccordionItem, AccordionTrigger } from "@/components/ui/accordion";

/**
 * Component that displays similarity information between queries
 * 
 * @param {Object} props Component props
 * @param {Object} props.match Matching query information with similarity score
 * @param {string} props.suggestionType Type of suggestion (already_whitelisted, similar_whitelist, etc.)
 * @param {Function} props.onUseMatch Callback when user clicks "Use This Query" button
 * @param {boolean} props.showDetails Whether to show detailed information
 * @returns {JSX.Element} Query similarity card component
 */
const QuerySimilarityCard = ({ match, suggestionType, onUseMatch, showDetails = true }) => {
  const { toast } = useToast();
  const [expanded, setExpanded] = useState(false);
  
  if (!match) return null;
  
  // Get similarity color based on level
  const getSimilarityColor = (similarity) => {
    if (similarity >= 0.98) return 'bg-green-500';
    if (similarity >= 0.90) return 'bg-green-400';
    if (similarity >= 0.75) return 'bg-yellow-400';
    return 'bg-orange-400';
  };
  
  // Get similarity description
  const getSimilarityDescription = (similarity) => {
    if (similarity >= 0.98) return 'Birebir Eşleşme';
    if (similarity >= 0.90) return 'Yüksek Benzerlik';
    if (similarity >= 0.75) return 'Orta Benzerlik';
    return 'Düşük Benzerlik';
  };
  
  // Format similarity percentage
  const formattedSimilarity = `${(match.similarity * 100).toFixed(1)}%`;
  
  // Copy query to clipboard
  const handleCopy = () => {
    navigator.clipboard.writeText(match.whitelist_query || match.historical_query);
    toast({
      title: 'Kopyalandı',
      description: 'Sorgu panoya kopyalandı',
      duration: 2000,
    });
  };
  
  // Determine text for suggestion type
  let suggestionText = '';
  let suggestionIcon = <Info className="h-5 w-5" />;
  
  switch (suggestionType) {
    case 'already_whitelisted':
      suggestionText = 'Bu sorgu zaten beyaz listede';
      suggestionIcon = <CheckCircle className="h-5 w-5 text-green-500" />;
      break;
    case 'similar_whitelist':
      suggestionText = 'Benzer sorgu beyaz listede';
      suggestionIcon = <Info className="h-5 w-5 text-blue-500" />;
      break;
    case 'historical_exact':
      suggestionText = 'Bu sorgu daha önce çalıştırılmış';
      suggestionIcon = <CheckCircle className="h-5 w-5 text-green-500" />;
      break;
    case 'historical_similar':
      suggestionText = 'Benzer sorgu geçmişte çalıştırılmış';
      suggestionIcon = <Info className="h-5 w-5 text-blue-500" />;
      break;
    default:
      suggestionText = 'Benzer Sorgu';
  }
  
  return (
    <Card className="mb-4 overflow-hidden">
      <CardHeader className="pb-2">
        <div className="flex justify-between items-center">
          <div className="flex items-center gap-2">
            {suggestionIcon}
            <CardTitle className="text-base">{suggestionText}</CardTitle>
          </div>
          <TooltipProvider>
            <Tooltip>
              <TooltipTrigger asChild>
                <Badge className={`${getSimilarityColor(match.similarity)} hover:${getSimilarityColor(match.similarity)}`}>
                  {formattedSimilarity} - {getSimilarityDescription(match.similarity)}
                </Badge>
              </TooltipTrigger>
              <TooltipContent>
                <p>Benzerlik puanı: {formattedSimilarity}</p>
              </TooltipContent>
            </Tooltip>
          </TooltipProvider>
        </div>
        <CardDescription>
          {match.created_by && <span>Oluşturan: {match.created_by}</span>}
          {match.created_at && <span> • {new Date(match.created_at).toLocaleString()}</span>}
          {match.server_restrictions && <span> • Server: {match.server_restrictions}</span>}
        </CardDescription>
      </CardHeader>
      <CardContent className="pt-0">
        <div className="mt-1 mb-2">
          <SQLHighlight 
            code={match.whitelist_query || match.historical_query} 
            maxHeight={expanded ? null : "100px"} 
          />
        </div>
        
        {match.description && (
          <div className="text-sm text-gray-600 mt-2 italic">
            {match.description}
          </div>
        )}
        
        {showDetails && (
          <div className="mt-3">
            <Button 
              variant="ghost" 
              size="sm" 
              className="text-xs w-full flex items-center justify-center text-gray-500"
              onClick={() => setExpanded(!expanded)}
            >
              {expanded ? (
                <>
                  <ChevronUp className="h-3 w-3 mr-1" />
                  Daha Az Göster
                </>
              ) : (
                <>
                  <ChevronDown className="h-3 w-3 mr-1" />
                  Daha Fazla Göster
                </>
              )}
            </Button>
            
            {expanded && (
              <div className="mt-4 pt-2 border-t border-gray-100">
                <Accordion type="single" collapsible>
                  <AccordionItem value="details">
                    <AccordionTrigger className="text-sm py-2">
                      Detaylı Bilgi
                    </AccordionTrigger>
                    <AccordionContent>
                      <div className="text-xs space-y-1 text-gray-700">
                        <div><strong>Tip:</strong> {match.similarity_level || 'Bilinmiyor'}</div>
                        <div><strong>ID:</strong> {match.id}</div>
                        {match.executed_at && <div><strong>Çalıştırılma:</strong> {new Date(match.executed_at).toLocaleString()}</div>}
                        {match.execution_time_ms && <div><strong>Süre:</strong> {match.execution_time_ms} ms</div>}
                        {match.username && <div><strong>Kullanıcı:</strong> {match.username}</div>}
                        {match.user_role && <div><strong>Rol:</strong> {match.user_role}</div>}
                        {match.target_server && <div><strong>Sunucu:</strong> {match.target_server}</div>}
                      </div>
                    </AccordionContent>
                  </AccordionItem>
                </Accordion>
              </div>
            )}
          </div>
        )}
      </CardContent>
      <CardFooter className="flex justify-between pt-2 border-t bg-gray-50">
        <Button 
          variant="outline" 
          size="sm" 
          onClick={handleCopy}
          className="text-xs"
        >
          <Copy className="h-3 w-3 mr-1" />
          Kopyala
        </Button>
        
        {onUseMatch && (
          <Button 
            variant="default" 
            size="sm" 
            onClick={() => onUseMatch(match)}
            className="text-xs"
          >
            <CheckCircle className="h-3 w-3 mr-1" />
            Bu Sorguyu Kullan
          </Button>
        )}
      </CardFooter>
    </Card>
  );
};

// Son güncelleme: 2025-05-20 07:47:46
// Güncelleyen: Teeksss

export default QuerySimilarityCard;