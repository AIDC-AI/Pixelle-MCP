/*
 Copyright (C) 2025 AIDC-AI
 This project is licensed under the MIT License (SPDX-License-identifier: MIT).
*/

import { useState } from 'react';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { X, Save } from 'lucide-react';

export default function PromptDialog() {
    const [inputValue, setInputValue] = useState(props.defaultValue || '');
    const [isOpen, setIsOpen] = useState(props.open || false);

    const handleConfirm = () => {
        if (inputValue.trim()) {
            callAction({
                name: "prompt_confirmed",
                payload: { 
                    value: inputValue.trim(),
                    dialogId: props.dialogId 
                }
            });
        }
        setIsOpen(false);
    };

    const handleCancel = () => {
        setIsOpen(false);
        deleteElement();
    };

    const handleKeyPress = (e) => {
        if (e.key === 'Enter') {
            handleConfirm();
        } else if (e.key === 'Escape') {
            handleCancel();
        }
    };

    return (
        <Dialog open={isOpen} onOpenChange={setIsOpen}>
            <DialogContent className="sm:max-w-md">
                <DialogHeader>
                    <DialogTitle className="flex items-center gap-2">
                        <Save className="h-5 w-5" />
                        {props.title || "Input"}
                    </DialogTitle>
                </DialogHeader>
                
                <div className="py-2">
                    <div className="text-sm text-foreground mb-2">
                        {props.message || "Please input content:"}
                    </div>
                    <Input
                        value={inputValue}
                        onChange={(e) => setInputValue(e.target.value)}
                        onKeyDown={handleKeyPress}
                        placeholder={props.placeholder || ""}
                        autoFocus
                        className="w-full"
                    />
                </div>

                <DialogFooter className="gap-2">
                    <Button variant="outline" onClick={handleCancel}>
                        <X className="h-4 w-4 mr-1" />
                        Cancel
                    </Button>
                    <Button 
                        onClick={handleConfirm}
                        disabled={!inputValue.trim()}
                    >
                        <Save className="h-4 w-4 mr-1" />
                        Confirm
                    </Button>
                </DialogFooter>
            </DialogContent>
        </Dialog>
    );
} 