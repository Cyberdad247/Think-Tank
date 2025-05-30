import React, { useState, useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { MessageSquare, X, Send, ThumbsUp, ThumbsDown, Smile, Frown, Meh } from 'react-feather';

/**
 * FeedbackCollector component for gathering user feedback.
 * 
 * Features:
 * - Floating feedback button
 * - Multiple feedback types (rating, text, emoji)
 * - Animated transitions
 * - Accessibility support
 * - Analytics integration
 * - Customizable appearance
 */

interface FeedbackCollectorProps {
  /** Position of the feedback button */
  position?: 'bottom-right' | 'bottom-left' | 'top-right' | 'top-left';
  /** Primary color for the feedback UI */
  primaryColor?: string;
  /** Function to call when feedback is submitted */
  onSubmit?: (feedback: FeedbackData) => Promise<void>;
  /** Whether to show the feedback button initially */
  initiallyVisible?: boolean;
  /** Custom trigger button content */
  triggerContent?: React.ReactNode;
  /** Whether to collect contact information */
  collectContactInfo?: boolean;
  /** Whether to allow screenshots */
  allowScreenshots?: boolean;
}

interface FeedbackData {
  type: 'rating' | 'text' | 'emoji';
  value: number | string;
  message?: string;
  email?: string;
  screenshot?: string;
  metadata: {
    url: string;
    timestamp: string;
    userAgent: string;
    sessionId?: string;
  };
}

export const FeedbackCollector: React.FC<FeedbackCollectorProps> = ({
  position = 'bottom-right',
  primaryColor = '#4F46E5', // Indigo-600
  onSubmit,
  initiallyVisible = true,
  triggerContent,
  collectContactInfo = false,
  allowScreenshots = false,
}) => {
  // State
  const [isOpen, setIsOpen] = useState(false);
  const [feedbackType, setFeedbackType] = useState<'rating' | 'text' | 'emoji'>('rating');
  const [rating, setRating] = useState<number | null>(null);
  const [emoji, setEmoji] = useState<'happy' | 'neutral' | 'sad' | null>(null);
  const [message, setMessage] = useState('');
  const [email, setEmail] = useState('');
  const [screenshot, setScreenshot] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isSubmitted, setIsSubmitted] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isVisible, setIsVisible] = useState(initiallyVisible);
  
  // Refs
  const containerRef = useRef<HTMLDivElement>(null);
  const messageInputRef = useRef<HTMLTextAreaElement>(null);
  
  // Position styles
  const positionStyles = {
    'bottom-right': 'bottom-4 right-4',
    'bottom-left': 'bottom-4 left-4',
    'top-right': 'top-4 right-4',
    'top-left': 'top-4 left-4',
  };
  
  // Animation variants
  const containerVariants = {
    hidden: { opacity: 0, scale: 0.8, y: 10 },
    visible: { opacity: 1, scale: 1, y: 0 },
    exit: { opacity: 0, scale: 0.8, y: 10 }
  };
  
  const buttonVariants = {
    rest: { scale: 1 },
    hover: { scale: 1.1 }
  };
  
  // Handle click outside to close
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (containerRef.current && !containerRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    };
    
    if (isOpen) {
      document.addEventListener('mousedown', handleClickOutside);
    }
    
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, [isOpen]);
  
  // Focus message input when feedback type changes to text
  useEffect(() => {
    if (feedbackType === 'text' && messageInputRef.current) {
      messageInputRef.current.focus();
    }
  }, [feedbackType]);
  
  // Handle taking screenshot
  const handleTakeScreenshot = async () => {
    if (!allowScreenshots) return;
    
    try {
      // This is a simplified implementation
      // In a real app, you would use a library like html2canvas
      // or a browser extension API to capture the screenshot
      
      // For now, we'll just simulate a screenshot with a placeholder
      setScreenshot('data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg==');
    } catch (err) {
      console.error('Failed to take screenshot:', err);
      setError('Failed to take screenshot. Please try again.');
    }
  };
  
  // Handle feedback submission
  const handleSubmit = async () => {
    // Validate input
    if (feedbackType === 'rating' && rating === null) {
      setError('Please select a rating');
      return;
    }
    
    if (feedbackType === 'emoji' && emoji === null) {
      setError('Please select an emoji');
      return;
    }
    
    if (feedbackType === 'text' && !message.trim()) {
      setError('Please enter a message');
      return;
    }
    
    if (collectContactInfo && email && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
      setError('Please enter a valid email address');
      return;
    }
    
    setError(null);
    setIsSubmitting(true);
    
    try {
      // Prepare feedback data
      const feedbackData: FeedbackData = {
        type: feedbackType,
        value: feedbackType === 'rating' ? rating! : 
               feedbackType === 'emoji' ? emoji! : 
               message,
        message: message || undefined,
        email: email || undefined,
        screenshot: screenshot || undefined,
        metadata: {
          url: window.location.href,
          timestamp: new Date().toISOString(),
          userAgent: navigator.userAgent,
          sessionId: localStorage.getItem('sessionId') || undefined
        }
      };
      
      // Submit feedback
      if (onSubmit) {
        await onSubmit(feedbackData);
      } else {
        // Default implementation - log to console
        console.log('Feedback submitted:', feedbackData);
        
        // Simulate API call
        await new Promise(resolve => setTimeout(resolve, 1000));
      }
      
      // Show success state
      setIsSubmitting(false);
      setIsSubmitted(true);
      
      // Reset form after delay
      setTimeout(() => {
        setIsOpen(false);
        
        // Reset form after closing
        setTimeout(() => {
          setRating(null);
          setEmoji(null);
          setMessage('');
          setEmail('');
          setScreenshot(null);
          setIsSubmitted(false);
          setFeedbackType('rating');
        }, 300);
      }, 2000);
      
    } catch (err) {
      console.error('Failed to submit feedback:', err);
      setIsSubmitting(false);
      setError('Failed to submit feedback. Please try again.');
    }
  };
  
  // Toggle visibility of the feedback button
  const toggleVisibility = () => {
    setIsVisible(!isVisible);
  };
  
  // Render emoji feedback option
  const renderEmojiOption = () => (
    <div className="space-y-4">
      <h3 className="text-lg font-medium text-gray-900">How are you feeling?</h3>
      
      <div className="flex justify-center space-x-6">
        <button
          type="button"
          onClick={() => setEmoji('happy')}
          className={`p-3 rounded-full transition-colors ${
            emoji === 'happy' ? 'bg-green-100 text-green-600' : 'text-gray-400 hover:text-green-600'
          }`}
          aria-label="Happy"
        >
          <Smile size={32} />
        </button>
        
        <button
          type="button"
          onClick={() => setEmoji('neutral')}
          className={`p-3 rounded-full transition-colors ${
            emoji === 'neutral' ? 'bg-yellow-100 text-yellow-600' : 'text-gray-400 hover:text-yellow-600'
          }`}
          aria-label="Neutral"
        >
          <Meh size={32} />
        </button>
        
        <button
          type="button"
          onClick={() => setEmoji('sad')}
          className={`p-3 rounded-full transition-colors ${
            emoji === 'sad' ? 'bg-red-100 text-red-600' : 'text-gray-400 hover:text-red-600'
          }`}
          aria-label="Sad"
        >
          <Frown size={32} />
        </button>
      </div>
    </div>
  );
  
  // Render rating feedback option
  const renderRatingOption = () => (
    <div className="space-y-4">
      <h3 className="text-lg font-medium text-gray-900">How would you rate your experience?</h3>
      
      <div className="flex justify-center space-x-2">
        {[1, 2, 3, 4, 5].map((value) => (
          <button
            key={value}
            type="button"
            onClick={() => setRating(value)}
            className={`w-10 h-10 rounded-full flex items-center justify-center text-lg font-medium transition-colors ${
              rating === value 
                ? `bg-${primaryColor} text-white` 
                : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
            }`}
            style={{ 
              backgroundColor: rating === value ? primaryColor : undefined,
              color: rating === value ? 'white' : undefined
            }}
            aria-label={`Rate ${value} out of 5`}
          >
            {value}
          </button>
        ))}
      </div>
    </div>
  );
  
  // Render text feedback option
  const renderTextOption = () => (
    <div className="space-y-4">
      <h3 className="text-lg font-medium text-gray-900">Share your thoughts</h3>
      
      <textarea
        ref={messageInputRef}
        value={message}
        onChange={(e) => setMessage(e.target.value)}
        className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
        rows={4}
        placeholder="What's on your mind?"
        aria-label="Feedback message"
      />
    </div>
  );
  
  // Render feedback type selector
  const renderFeedbackTypeSelector = () => (
    <div className="flex border border-gray-200 rounded-lg overflow-hidden mb-4">
      <button
        type="button"
        onClick={() => setFeedbackType('rating')}
        className={`flex-1 py-2 px-4 text-sm font-medium ${
          feedbackType === 'rating' 
            ? 'bg-gray-100 text-gray-900' 
            : 'bg-white text-gray-500 hover:text-gray-700 hover:bg-gray-50'
        }`}
        aria-label="Rating feedback"
        aria-pressed={feedbackType === 'rating'}
      >
        Rating
      </button>
      
      <button
        type="button"
        onClick={() => setFeedbackType('emoji')}
        className={`flex-1 py-2 px-4 text-sm font-medium ${
          feedbackType === 'emoji' 
            ? 'bg-gray-100 text-gray-900' 
            : 'bg-white text-gray-500 hover:text-gray-700 hover:bg-gray-50'
        }`}
        aria-label="Emoji feedback"
        aria-pressed={feedbackType === 'emoji'}
      >
        Emoji
      </button>
      
      <button
        type="button"
        onClick={() => setFeedbackType('text')}
        className={`flex-1 py-2 px-4 text-sm font-medium ${
          feedbackType === 'text' 
            ? 'bg-gray-100 text-gray-900' 
            : 'bg-white text-gray-500 hover:text-gray-700 hover:bg-gray-50'
        }`}
        aria-label="Text feedback"
        aria-pressed={feedbackType === 'text'}
      >
        Text
      </button>
    </div>
  );
  
  // Render contact info form
  const renderContactInfo = () => (
    <div className="mt-4">
      <label htmlFor="feedback-email" className="block text-sm font-medium text-gray-700 mb-1">
        Email (optional)
      </label>
      <input
        type="email"
        id="feedback-email"
        value={email}
        onChange={(e) => setEmail(e.target.value)}
        className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
        placeholder="your@email.com"
      />
      <p className="mt-1 text-xs text-gray-500">
        We'll only use this to follow up on your feedback if needed.
      </p>
    </div>
  );
  
  // Render screenshot option
  const renderScreenshotOption = () => (
    <div className="mt-4">
      <button
        type="button"
        onClick={handleTakeScreenshot}
        className="flex items-center text-sm text-gray-600 hover:text-gray-900"
        disabled={!!screenshot}
      >
        {screenshot ? (
          <span className="text-green-600">✓ Screenshot captured</span>
        ) : (
          <>
            <svg className="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 9a2 2 0 012-2h.93a2 2 0 001.664-.89l.812-1.22A2 2 0 0110.07 4h3.86a2 2 0 011.664.89l.812 1.22A2 2 0 0018.07 7H19a2 2 0 012 2v9a2 2 0 01-2 2H5a2 2 0 01-2-2V9z" />
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 13a3 3 0 11-6 0 3 3 0 016 0z" />
            </svg>
            Include screenshot
          </>
        )}
      </button>
      
      {screenshot && (
        <div className="mt-2 relative">
          <img 
            src={screenshot} 
            alt="Screenshot" 
            className="w-full h-20 object-cover rounded border border-gray-300" 
          />
          <button
            type="button"
            onClick={() => setScreenshot(null)}
            className="absolute top-1 right-1 bg-white rounded-full p-1 shadow-sm hover:bg-gray-100"
            aria-label="Remove screenshot"
          >
            <X size={14} />
          </button>
        </div>
      )}
    </div>
  );
  
  // Render success message
  const renderSuccessMessage = () => (
    <div className="text-center py-6">
      <div className="mx-auto flex items-center justify-center h-12 w-12 rounded-full bg-green-100">
        <svg className="h-6 w-6 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
        </svg>
      </div>
      <h3 className="mt-3 text-lg font-medium text-gray-900">Thank you for your feedback!</h3>
      <p className="mt-2 text-sm text-gray-500">
        Your input helps us improve our product.
      </p>
    </div>
  );
  
  return (
    <>
      {/* Feedback button */}
      {isVisible && (
        <motion.div
          className={`fixed z-50 ${positionStyles[position]}`}
          initial={{ opacity: 0, scale: 0.8 }}
          animate={{ opacity: 1, scale: 1 }}
          exit={{ opacity: 0, scale: 0.8 }}
          transition={{ duration: 0.2 }}
        >
          <motion.button
            type="button"
            onClick={() => setIsOpen(true)}
            className="flex items-center justify-center w-12 h-12 rounded-full shadow-lg focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
            style={{ backgroundColor: primaryColor }}
            aria-label="Open feedback form"
            variants={buttonVariants}
            initial="rest"
            whileHover="hover"
            whileTap={{ scale: 0.95 }}
          >
            {triggerContent || <MessageSquare className="text-white" size={20} />}
          </motion.button>
        </motion.div>
      )}
      
      {/* Feedback modal */}
      <AnimatePresence>
        {isOpen && (
          <div className="fixed inset-0 z-50 overflow-y-auto">
            <div className="flex items-end justify-center min-h-screen pt-4 px-4 pb-20 text-center sm:block sm:p-0">
              <div className="fixed inset-0 transition-opacity" aria-hidden="true">
                <div className="absolute inset-0 bg-gray-500 opacity-75"></div>
              </div>
              
              <motion.div
                ref={containerRef}
                className="inline-block align-bottom bg-white rounded-lg text-left overflow-hidden shadow-xl transform transition-all sm:my-8 sm:align-middle sm:max-w-lg sm:w-full"
                variants={containerVariants}
                initial="hidden"
                animate="visible"
                exit="exit"
              >
                <div className="bg-white px-4 pt-5 pb-4 sm:p-6 sm:pb-4">
                  <div className="sm:flex sm:items-start">
                    <div className="w-full">
                      {/* Header */}
                      <div className="flex justify-between items-center mb-4">
                        <h2 className="text-xl font-bold text-gray-900">
                          Share Your Feedback
                        </h2>
                        <button
                          type="button"
                          onClick={() => setIsOpen(false)}
                          className="bg-white rounded-md text-gray-400 hover:text-gray-500 focus:outline-none focus:ring-2 focus:ring-blue-500"
                          aria-label="Close"
                        >
                          <X size={20} />
                        </button>
                      </div>
                      
                      {/* Content */}
                      {isSubmitted ? (
                        renderSuccessMessage()
                      ) : (
                        <div>
                          {/* Feedback type selector */}
                          {renderFeedbackTypeSelector()}
                          
                          {/* Feedback form based on type */}
                          <div className="mt-4">
                            {feedbackType === 'rating' && renderRatingOption()}
                            {feedbackType === 'emoji' && renderEmojiOption()}
                            {feedbackType === 'text' && renderTextOption()}
                            
                            {/* Additional message field for rating and emoji */}
                            {(feedbackType === 'rating' || feedbackType === 'emoji') && (
                              <div className="mt-4">
                                <label htmlFor="feedback-message" className="block text-sm font-medium text-gray-700 mb-1">
                                  Additional comments (optional)
                                </label>
                                <textarea
                                  id="feedback-message"
                                  value={message}
                                  onChange={(e) => setMessage(e.target.value)}
                                  className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                                  rows={3}
                                  placeholder="Tell us more..."
                                />
                              </div>
                            )}
                            
                            {/* Contact info */}
                            {collectContactInfo && renderContactInfo()}
                            
                            {/* Screenshot option */}
                            {allowScreenshots && renderScreenshotOption()}
                            
                            {/* Error message */}
                            {error && (
                              <div className="mt-4 text-sm text-red-600">
                                {error}
                              </div>
                            )}
                          </div>
                        </div>
                      )}
                    </div>
                  </div>
                </div>
                
                {/* Footer */}
                {!isSubmitted && (
                  <div className="bg-gray-50 px-4 py-3 sm:px-6 sm:flex sm:flex-row-reverse">
                    <button
                      type="button"
                      onClick={handleSubmit}
                      className="w-full inline-flex justify-center rounded-md border border-transparent shadow-sm px-4 py-2 text-base font-medium text-white focus:outline-none focus:ring-2 focus:ring-offset-2 sm:ml-3 sm:w-auto sm:text-sm"
                      style={{ backgroundColor: primaryColor }}
                      disabled={isSubmitting}
                    >
                      {isSubmitting ? (
                        <svg className="animate-spin -ml-1 mr-2 h-4 w-4 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                          <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                          <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                        </svg>
                      ) : (
                        <Send size={16} className="mr-2" />
                      )}
                      {isSubmitting ? 'Submitting...' : 'Submit Feedback'}
                    </button>
                    <button
                      type="button"
                      onClick={() => setIsOpen(false)}
                      className="mt-3 w-full inline-flex justify-center rounded-md border border-gray-300 shadow-sm px-4 py-2 bg-white text-base font-medium text-gray-700 hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 sm:mt-0 sm:ml-3 sm:w-auto sm:text-sm"
                      disabled={isSubmitting}
                    >
                      Cancel
                    </button>
                  </div>
                )}
              </motion.div>
            </div>
          </div>
        )}
      </AnimatePresence>
    </>
  );
};