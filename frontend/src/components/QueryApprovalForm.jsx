import React, { useState } from 'react';
import { useToast } from '@/components/ui/use-toast';
import { Button } from '@/components/ui/button';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Switch } from '@/components/ui/switch';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { AlertTriangle, ArrowRight, CheckCircle, Info, Send, Shield } from 'lucide-react';
import SQLHighlight from './SQLHighlight';
import { requestQueryApproval } from '@/api/queries';

const QueryApprovalForm = ({ 
  query, 
  server, 
  onSubmitSuccess = () => {}, 
  onCancel = () => {} 
}) => {
  const [justification, setJustification] = useState('');
  const [priority, setPriority] = useState('normal');
  const [willRepeat, setWillRepeat] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const { toast } = useToast();
  
  // Submit form to request approval
  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!query || !server) {
      toast({
        title: "Eksik Bilgi",
        description: "Sorgu ve sunucu bilgisi gereklidir.",
        variant: "destructive",
      });
      return;
    }
    
    if (!justification.trim()) {
      toast({
        title: "Gerekçe Girilmeli",
        description: "Lütfen sorgu için bir gerekçe belirtin.",
        variant: "destructive",
      });
      return;
    }
    
    setIsSubmitting(true);
    
    try {
      // Call the API to request approval
      const result = await requestQueryApproval({
        sql_query: query,
        server_alias: server,
        justification,
        priority,
        will_repeat: willRepeat
      });
      
      toast({
        title: "Başarılı",
        description: "Sorgu onay talebi gönderildi. Onaylandığında bildirim alacaksınız.",
        variant: "default",
      });
      
      onSubmitSuccess(result);
    } catch (error) {
      console.error('Error requesting query approval:', error);
      toast({
        title: "Hata",
        description: "Sorgu onay talebi gönderilirken bir hata oluştu.",
        variant: "destructive",
      });
    } finally {
      setIsSubmitting(false);
    }
  };
  
  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div className="space-y-2">
        <Label>Sorgu</Label>
        <SQLHighlight code={query} />
      </div>
      
      <div className="space-y-2">
        <Label>Hedef Sunucu</Label>
        <div className="p-2 border rounded-md bg-gray-50">
          <p className="text-gray-800 font-medium">{server}</p>
        </div>
      </div>
      
      <div className="space-y-2">
        <Label htmlFor="justification">Gerekçe</Label>
        <Textarea
          id="justification"
          placeholder="Bu sorguya neden ihtiyacınız olduğunu ve neden onaylanması gerektiğini açıklayın..."
          value={justification}
          onChange={(e) => setJustification(e.target.value)}
          rows={3}
          required
        />
      </div>
      
      <div className="space-y-2">
        <Label htmlFor="priority">Öncelik</Label>
        <Select id="priority" value={priority} onValueChange={setPriority}>
          <SelectTrigger>
            <SelectValue placeholder="Öncelik seçin" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="low">
              <div className="flex items-center">
                <div className="w-2 h-2 rounded-full bg-blue-500 mr-2"></div>
                <span>Düşük</span>
              </div>
            </SelectItem>
            <SelectItem value="normal">
              <div className="flex items-center">
                <div className="w-2 h-2 rounded-full bg-green-500 mr-2"></div>
                <span>Normal</span>
              </div>
            </SelectItem>
            <SelectItem value="high">
              <div className="flex items-center">
                <div className="w-2 h-2 rounded-full bg-amber-500 mr-2"></div>
                <span>Yüksek</span>
              </div>
            </SelectItem>
            <SelectItem value="urgent">
              <div className="flex items-center">
                <div className="w-2 h-2 rounded-full bg-red-500 mr-2"></div>
                <span>Acil</span>
              </div>
            </SelectItem>
          </SelectContent>
        </Select>
      </div>
      
      <div className="flex items-center space-x-2">
        <Switch
          id="will-repeat"
          checked={willRepeat}
          onCheckedChange={setWillRepeat}
        />
        <Label htmlFor="will-repeat">Bu sorguyu düzenli olarak kullanacağım (beyaz listeye eklenebilir)</Label>
      </div>
      
      <div className="bg-blue-50 p-3 rounded-md">
        <div className="flex">
          <Info className="h-5 w-5 text-blue-500 mr-2 flex-shrink-0" />
          <div>
            <p className="text-sm font-medium text-blue-800">Onay Süreci</p>
            <p className="text-sm text-blue-700 mt-1">
              Onay talebiniz yöneticilere iletilecek ve incelenecektir. Sonuç hakkında bilgilendirileceksiniz.
              {willRepeat && " Onaylanması durumunda, bu sorgu beyaz listeye eklenebilir ve gelecekte otomatik onay alabilir."}
            </p>
          </div>
        </div>
      </div>
      
      <div className="flex justify-end space-x-2 pt-2">
        <Button
          type="button"
          variant="outline"
          onClick={onCancel}
        >
          İptal
        </Button>
        <Button
          type="submit"
          disabled={isSubmitting || !justification.trim()}
        >
          {isSubmitting ? (
            <>
              <div className="animate-spin mr-2 h-4 w-4 border-2 border-white border-t-transparent rounded-full" />
              Gönderiliyor...
            </>
          ) : (
            <>
              <Send className="h-4 w-4 mr-2" />
              Onay İste
            </>
          )}
        </Button>
      </div>
    </form>
  );
};

// Son güncelleme: 2025-05-20 05:50:02
// Güncelleyen: Teeksss

export default QueryApprovalForm;